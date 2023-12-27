import pandas as pd

df = pd.read_html('/home/veronica/Downloads/Boxscore.html')
print(df[0])
#csv = df[4].to_csv('apa.csv', index=False)
df[0].to_csv('apa.csv')

print(df)