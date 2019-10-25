import pandas as pd
import numpy as np
import time


def read_data(tabname, tabkey):

    return pd.read_csv(tabname, index_col=tabkey)

def bin_trans(var, sp_list):
    # sp_list = [1, 3.5]
    for i, vi in enumerate(sp_list):
        if var <= vi:
            bin = i + 1
            break
        else:
            bin = len(sp_list) + 1
    return bin
# bin_trans(12, [1, 3.5, 11])

def woe_trans(var, sp_list, woe_list):

    for i, vi in enumerate(sp_list):
        if var <= vi:
            woe = woe_list[i]
            break
        else:
            woe = woe_list[len(woe_list) - 1]

    return woe





def get_bin(tabname, varname, sp_list):


    tab1 = tabname.copy()
    # tabname['bin'] = tabname.apply(lambda x :bin_trans(tabname[varname]), axis=1, **sp_list)
    kwds = {"sp_list":sp_list}
    tab1['bin'] = tab1[varname].apply(bin_trans, **kwds)

    return tab1[['target', 'bin']]

# test = get_bin(data1, 'td_id_3m', [1, 3.5])



def get_bound(sp_list):

    # sp_list = [1, 3.5]
    ul = sp_list.copy()
    ll = sp_list.copy()
    ul.append(float("inf"))
    ll.insert(0, float("-inf"))

    sp_dict = {'bin': [i + 1 for i in list(range(len(sp_list) + 1))], 'll':ll, 'ul':ul}
    return pd.DataFrame(sp_dict)


def get_dist(df, t0, t1):
    '''
    
    :param df: 
    :param t0: t0和t1以全部数据来计算woe和iv
    :param t1: 
    :return: 
    '''
    # t_sum = pd.pivot_table(df, index='bin', columns='target', values='one', aggfunc=[np.sum])
    # t1 = df.target.sum()
    # t0 = len(df) - t1
    t_sum = df.groupby(['bin'])['target', 'one'].sum()
    t_sum.rename(columns={'target':'p1'}, inplace=True)
    t_sum['p0'] = t_sum['one'] - t_sum['p1']
    t_sum.reset_index(level=0, inplace=True)

    t_sum['p1_r'] = t_sum['p1'] / t1
    t_sum['p0_r'] = t_sum['p0'] / t0
    t_sum['woe'] = np.log(t_sum['p1_r'] / t_sum['p0_r'])
    t_sum['iv0'] = (t_sum['p1_r'] - t_sum['p0_r']) * t_sum['woe']

    t_sum.drop(['one', 'p0_r', 'p1_r'], axis=1, inplace=True)
    return t_sum

def get_mapiv_result(tabname, varname, sp_list, t0, t1):

    boundry = get_bound(sp_list)
    bin = get_bin(tabname, varname, sp_list)

    bin['one'] = 1
    mapiv1 = get_dist(bin, t0, t1)

    return boundry.merge(mapiv1, on='bin')

# test = pd.DataFrame({'bin':[0,1,1,2,3,0,0,3,2],'target':[0,0,1,0,0,1,1,1,1]})
# test['one'] = 1
# test1 = get_dist(test)
#
# test1.index


def get_iv(intab, varname, split_i, min_num):
    data_l = intab[intab[varname] <= split_i]
    data_u = intab[intab[varname] > split_i]

    p1 = intab['target'].sum()
    p0 = len(intab) - p1

    if p1 > 0 and p0 > 0 :        #分割后的数据满足最小分组数要求
        p1_l = data_l['target'].sum()
        p0_l = len(data_l) - p1_l

        p1_u, p0_u = p1-p1_l, p0-p0_l
        if p0_l > 0 and p0_u > 0 and p1_l > 0 and p1_u > 0 and (p0_l + p1_l) >= min_num and (p0_u + p1_u) >= min_num:

            woe_l = np.log((p1_l / p1) / (p0_l / p0))
            iv_l = (p1_l / p1 - p0_l / p0) * np.log((p1_l / p1) / (p0_l / p0))
            woe_u = np.log((p1_u / p1) / (p0_u / p0))
            iv_u = (p1_u / p1 - p0_u / p0) * np.log((p1_u / p1) / (p0_u / p0))
        else: return (0, 0)
      # iv = iv_l + iv_u
    else: return (0, 0)
    return (iv_l + iv_u, np.float(woe_l < woe_u))



def split_var_bin(tabname, varname, woe_direct, min_num):

    t1 = np.unique(tabname[varname])
    if len(t1) > 1:
        t2 = [(t1[i]+t1[i+1])/2.0 for i in range(len(t1)-1)] #切割点平均值
        t3 = [(i, get_iv(tabname, varname, i, min_num)) for i in t2]
        t3_1 = [j for j in t3 if j[1][1] == woe_direct and j[1][0] >= 0.001] #与首次切割方向相同
        if len(t3_1) > 0:

            t3_max = [i[1][0] for i in t3_1]
            max_index = t3_max.index(max(t3_max))

            split_value = [t3_1[max_index][0]]

            tab_l = tabname[tabname[varname] <= split_value]
            tab_u = tabname[tabname[varname] > split_value]

            split_value_i = split_var_bin(tab_l, varname, woe_direct, min_num)
            split_value_j = split_var_bin(tab_u, varname, woe_direct, min_num)
        else:return []
    else:return []
    # return split_value.append(split_value_i.append(split_value_j))
    return split_value + split_value_i + split_value_j



def first_split(tabname, varname, min_num):
     # 第一次决定分割的woe方向

    t1 = np.unique(tabname[varname])
    t2 = [(t1[i] + t1[i + 1]) / 2.0 for i in range(len(t1) - 1)]  # 切割点平均值
    t3 = [(i, get_iv(tabname, varname, i, min_num)) for i in t2]
    # t3_1 = [j for j in t3 if j[1][0] >= 0.001]

    t3_max = [i[1][0] for i in t3]
    max_index = t3_max.index(max(t3_max))

    return t3[max_index][0], t3[max_index][1][1]

def get_nulldata_mapiv(tab, t0, t1):

    null_t1 = tab.target.sum()
    null_t0 = len(tab) - null_t1
    null_p1r = null_t1 / t1
    null_p0r = null_t0 / t0
    null_woe = np.log(null_p1r / null_p0r)
    null_iv = (null_p1r - null_p0r) * null_woe
    nullmapiv = pd.DataFrame({'bin':0, 'll':np.nan, 'ul':np.nan, 'p1':null_t1, 'p0':null_t0, 'woe':null_woe, 'iv0':null_iv}, index=[0])
    # nullmapiv = pd.DataFrame({'bin':[0], 'll':[np.nan], 'ul':[np.nan], 'p1':[null_t1], 'p0':[null_t0], 'woe':[null_woe], 'iv0':[null_iv]})

    return nullmapiv

def split_onevar(tabname, varname, min_num):

    t1 = tabname.target.sum()
    t0 = len(tabname) - t1

    nulltab = tabname[pd.isnull(tabname[varname])] #缺失值单独一箱
    n_nulltab = tabname[pd.isnull(tabname[varname]) == 0] #非缺失
    if len(np.unique(n_nulltab[varname])) > 1:
        split_value_1, woe_direct = first_split(n_nulltab, varname, min_num)

        tab_l = n_nulltab[n_nulltab[varname] <= split_value_1]
        tab_u = n_nulltab[n_nulltab[varname] > split_value_1]

        split_value = [split_value_1]
        split_value_l = split_var_bin(tab_l, varname, woe_direct, min_num)
        split_value_u = split_var_bin(tab_u, varname, woe_direct, min_num)

        sp_result = split_value + split_value_l + split_value_u
        sp_result.sort()

        n_nullmapiv = get_mapiv_result(n_nulltab, varname, sp_result, t0, t1) #非缺失值的分布，计算时传入t0,t1
    else:
        n_nullmapiv = pd.DataFrame()

    if len(nulltab) > 0:
        nullmapiv = get_nulldata_mapiv(nulltab, t0, t1)
    else:
        nullmapiv = pd.DataFrame()

    # print(sp_result)
    return pd.concat([nullmapiv, n_nullmapiv], axis=0)

def split_data(indata, min_group_rate):

    min_num = np.round(len(indata) * min_group_rate, 0)  # 限定最小分组数
    feature_list = list(indata)
    feature_list1 = [i for i in feature_list if 'target' not in i]

    mapiv = pd.DataFrame()
    for var_i in feature_list1:

        print(var_i)
        mapiv1 = split_onevar(indata[[var_i, 'target']], var_i, min_num)
        mapiv1['varname'] = var_i
        mapiv = pd.concat([mapiv1, mapiv], axis=0)

    m1 = mapiv.groupby(['varname'])[['iv0']].sum()
    m1.rename(columns={'iv0': 'iv'}, inplace=True)
    m1.reset_index(level=0, inplace=True)
    mapiv_t = mapiv.merge(m1, on='varname')

    return mapiv_t


def apply_woetab(indata, mapiv):

    outdata = indata.copy()
    var_list = np.unique(mapiv['varname'])
    for vi in var_list:

        ul_list = mapiv[mapiv['varname'] == vi]['ul'].values
        woe_list = mapiv[mapiv['varname'] == vi]['woe'].values
        kwds = {"sp_list":ul_list, "woe_list":woe_list}
        outdata['W_{}'.format(vi)] = outdata[vi].apply(woe_trans, **kwds)

    outdata_col = list(outdata)
    outdata_col_woe = [i for i in outdata_col if 'W_' in i]
    outdata_woe = outdata[['target'] + outdata_col_woe]
    return outdata_woe


