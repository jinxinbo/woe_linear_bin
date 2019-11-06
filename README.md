## woe_linear_bin

#### |- woe_bin
#####  |- linear_woe_bin.py
      |- split_data
         |- split_onevar
            |- first_split
               |- get_iv
            |- split_var_bin
               |- get_iv
            |- get_mapiv_result
               |- get_bound
               |- get_bin
                  |- bin_trans
               |- get_dist              
      |-apply_woetab
         |-woe_trans

## Example 
***the version 0.0.1 only can split the continuous variable, so if you have the category variable, 
you can use pd.get_dumies() translate into  continuous variable***

*now,suppose you have a DataFrame data0*

```python
import pandas as pd
import woe_bin
data1 = pd.get_dummies(data0)

mapiv_1 = woe_bin.split_data(data1, 'target', 0.1)  # 'target' is the Y , while 0.1 is the min_bin reate
```
*also,we can translate the origin data into woetab.*

```python
woetab = woe_bin.apply_woetab(data1, mapiv_1)
```
