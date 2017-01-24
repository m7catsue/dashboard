# 将CSV文件中的数据写入sqlite数据库
import pandas as pd
import sqlite3
import os

db_tmp = sqlite3.connect(r'C:\Users\m7catsue\PycharmProjects\WebDevelopment\dashboard\bokeh_test_demo\db_tmp.db')
curs = db_tmp.cursor()

current_dir = os.path.abspath(os.path.dirname(__file__))
csv_files = [file_name for file_name in os.listdir(current_dir)  # 得到所有后缀为csv的文件名称;os.listdir()只包含文件名和后缀
             if file_name.split('.')[-1] == 'csv']

# 将所有csv文件读入df_aqi
df_aqi = pd.read_csv(os.path.join(current_dir, csv_files[0]), encoding='gbk')
for file_name in csv_files[1:]:
    df_tmp = pd.read_csv(os.path.join(current_dir, file_name), encoding='gbk')
    df_aqi = pd.concat([df_aqi, df_tmp], ignore_index=True)
    print('[Status] Concatenated a CSV file.')

df_aqi.rename(columns={'Date (LST)': 'timestamp', 'Parameter': 'parameter',
                       'Site': 'city', 'Year': 'year', 'Month': 'month',
                       'Day': 'day', 'Hour': 'hour', 'Value': 'value', 'Duration': 'duration'},
              inplace=True)
df_aqi['date'] = pd.to_datetime(df_aqi['timestamp']).dt.date              # 写入sqlite后在读到dataframe中仍然为Object类型
df_aqi = df_aqi[['city', 'parameter', 'date',                             # 将所有timestamp仅保留date部分
                 'year', 'month', 'day', 'hour',
                 'value', 'duration']]

# 处理异常值('-999')并进行聚合运算
df_aqi['value'] = df_aqi['value'].apply(lambda x: 0 if x == -999 else x)  # 将默认缺失值-999替换为0
df_aqi = df_aqi.groupby(['city', 'date'])['value'].agg(['mean', 'min', 'max'])
df_aqi.reset_index(level=['city', 'date'], inplace=True)
df_aqi['mean'] = df_aqi['mean'].round(0).astype(int)                      # round到整数位

df_aqi['year'] = df_aqi['date'].astype(str).apply(lambda x: x[:4])
df_aqi.rename(columns={'mean': 'mean_val', 'max': 'max_val', 'min': 'min_val'},
              inplace=True)

df_aqi.to_sql(name='aqi_data', con=db_tmp)                                # table name: aqi_data

curs.close()
db_tmp.close()


