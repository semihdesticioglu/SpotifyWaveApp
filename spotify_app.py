from h2o_wave import Q, main, app, ui, site, data
import pandas as pd
import os 
import numpy as np 
from datetime import datetime
@app('/spotify')
async def serve(q: Q):
   

    q.page['Stream_History'] = ui.form_card(box='1 1 3 6', items=[
            ui.text_xl('Upload your Spotify Stream History',tooltip='It should be in Json format'),
            ui.file_upload(name='datasets', label='Upload', multiple=True),
       ])


    q.client.data_path = './data'
    if not os.path.exists(q.client.data_path):
        os.mkdir(q.client.data_path)
    if q.args.datasets:
        print("ok")
        await handle_uploaded_data(q)
    await q.page.save()

async def handle_uploaded_data(q: Q):
    data_path = q.client.data_path
    print(data_path)
    print(q.args.datasets[0])
    
    # Download new dataset to data directory
    q.client.working_file_path = await q.site.download(url=q.args.datasets[0], path=data_path)
    
    print(q.client.working_file_path)

    df = pd.read_json(q.client.working_file_path)

    df["endTime"] = pd.to_datetime(df["endTime"]) + pd.Timedelta(hours=3)
    df["Weekday"] = pd.to_datetime(df["endTime"], format='%Y-%m-%d %H:%M').dt.day_name()
    df["Hour"] = pd.to_datetime(df["endTime"], format='%Y-%m-%d %H:%M').dt.hour
    df['Month'] = pd.to_datetime(df["endTime"], format='%Y-%m-%d %H:%M').dt.strftime('%Y-%m')
    df['WeekdayOrNot'] = np.where(pd.to_datetime(df["endTime"], format='%Y-%m-%d %H:%M').dt.dayofweek < 5,0,1 )
    df["Minutes"] = df["msPlayed"] / 60000
    df["Minutes"] = df["Minutes"].round(decimals=1)
    df["PrevEndTime"] = df["endTime"].shift(1)
    df.loc[0, 'Session_Id'] = 1
    for i in range(1, len(df)):   
        if df.loc[i-1, 'endTime'] + pd.Timedelta(minutes=30)  < df.loc[i, 'endTime']  :  
             df.loc[i, "Session_Id"] = df.loc[i-1, 'Session_Id'] + 1
        else:
             df.loc[i, 'Session_Id'] = df.loc[i-1, 'Session_Id']
    df["endTime"] = df["endTime"].astype(str)
    df.drop(["msPlayed"],axis=1, inplace=True)
   
    print(df)
    #make a bar plot for hour analysis
    df_hour =  df.groupby("Hour").agg({"Minutes":"sum"}).reset_index()
    df_hour["Minutes"] = df_hour["Minutes"].astype(int)
    q.page.add('bar_plot', ui.plot_card(
    box='7 1 3 3',
    title='Total Minutes Played on Each Hour',
    data=data(fields=df_hour.columns.tolist(),rows=df_hour.values.tolist(),pack=True),
    plot=ui.plot([
        ui.mark(type='interval', 
        x='=Hour', y='=Minutes',y_min=0,color='blue',x_max=23)
    ])
    ))

    #make a bar plot for weekday analysis
    df_weekday =  df.groupby("Weekday").agg({"Minutes":"sum"}).reset_index()
    df_weekday["Minutes"] = df_weekday["Minutes"].astype(int)
    df_weekday['Weekday'] = pd.Categorical(
    df_weekday['Weekday'],  categories=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], ordered=True
         )
    df_weekday = df_weekday.sort_values('Weekday',ascending=True)
    q.page.add('bar_plot2', ui.plot_card(
    box='4 4 3 3',
    title='Total Minutes Played on Each Day',
    data=data(fields=df_weekday.columns.tolist(),rows=df_weekday.values.tolist(),pack=True),
    plot=ui.plot([
        ui.mark(type='interval', 
        x='=Weekday', y='=Minutes',y_min=0,color='blue')
    ])
    ))

    #make a bar plot for month analysis
    df_month =  df.groupby("Month").agg({"Minutes":"sum"}).reset_index()
    df_month["Minutes"] = df_month["Minutes"].astype(int)
    q.page.add('bar_plot3', ui.plot_card(
    box='7 4 3 3',
    title='Total Minutes Played on Each Month',
    data=data(fields=df_month.columns.tolist(),rows=df_month.values.tolist(),pack=True),
    plot=ui.plot([
        ui.mark(type='interval', 
        x='=Month', y='=Minutes',y_min=0,color='blue')
    ])
    ))

    #make a bar plot for most listened artists for each month
    df_monthly_artists = df.groupby(["Month","artistName"]).agg({"Minutes":"sum"}).reset_index().sort_values(["Month","artistName"],ascending=False)
    df_monthly_artists["Rank"] = df_monthly_artists.groupby("Month").rank(ascending=False, method='first')["Minutes"]
    df_monthly_artists = df_monthly_artists.loc[df_monthly_artists.Rank==1].sort_values(["Month"],ascending=True)
    df_monthly_artists["Minutes"] = df_monthly_artists["Minutes"].astype(int)

    q.page.add('bar_plot4', ui.plot_card(
    box='4 1 3 3',
    title='Most Played Artist for Each Month with Total Minutes Listened',
    data=data(fields=df_monthly_artists.columns.tolist(),rows=df_monthly_artists.values.tolist(),pack=True),
    plot=ui.plot([
        ui.mark(type='interval', 
        x='=Month', y='=Minutes',y_min=0,color='blue',label='=artistName',label_position='top')
    ])
    ))

    #make a line plot for most listened 5 artists with monthly trend
    df_top = df.groupby("artistName").agg({"Minutes":"sum"}).reset_index()
    df_top["Minutes"] = df_top["Minutes"].astype(int)
    df_top10 = df_top.sort_values("Minutes", ascending=False).head(5)
    df_artist1 = df.groupby(["Month","artistName"]).agg({"Minutes":"sum"}).reset_index()
    df_artist2 = df_artist1[df_artist1.artistName.isin(df_top10.artistName)]
    df_artist2["key"] = df_artist2["Month"] + df_artist2["artistName"]
    months = pd.DataFrame(df_artist2["Month"].unique())
    artists = pd.DataFrame(df_artist2["artistName"].unique() )
    months['key'] = 0
    artists['key'] = 0
    months_and_artists = months.merge(artists, how='outer', on = 'key')
    months_and_artists.drop('key',1, inplace=True)
    months_and_artists.columns = ["Month","artistName"]
    months_and_artists["key"] = months_and_artists["Month"] + months_and_artists["artistName"]
    months_and_artists = pd.merge(months_and_artists, df_artist2[["key","Minutes"]], how='left', on ='key')
    months_and_artists.drop('key',1, inplace=True)
    months_and_artists["Minutes"] = months_and_artists["Minutes"].fillna(0)
    
    q.page.add('line_plot5', ui.plot_card(
    box='8 7 5 4',
    title="Most Played Top 5 Artists and Their Monthly Listened Durations",
    data=data(fields=months_and_artists.columns.tolist(),rows=months_and_artists.values.tolist(),pack=True),
    plot=ui.plot([
        ui.mark(type='area', 
        x='=Month', y='=Minutes',y_min=0,color='=artistName')
    ])
    ))

    #make a info card about session count and time duration
    session_count = str(df.groupby("Session_Id").agg({"Minutes":"sum"}).count()[0])
    first_date = str(datetime.strptime(str(df.endTime.min()), '%Y-%m-%d %H:%M:%S').strftime('%d-%b-%Y').upper())
    avg_session_duration = str(round(df.groupby("Session_Id").agg({"Minutes":"sum"})["Minutes"].mean()))
    q.page.add('info_card', ui.form_card(
    box='1 7 3 2',
    items=[
        ui.text('Your session count is '+ session_count + ' since the date ' + first_date + '.', size='l', width='400px'),
        ui.separator('--------------------------------------------------------'),
        ui.text('Your average session length is ' + avg_session_duration + ' minutes.', size='l', width='400px')
    ]
    ))

    #make a info card about longest session
    longest_session_time = int(df.groupby("Session_Id").agg({"Minutes":"sum"}).sort_values(by=["Minutes"], ascending=False).head(1)['Minutes'].values[0])
    session_id  = df.groupby("Session_Id").agg({"Minutes":"sum"}).sort_values(by=["Minutes"], ascending=False).head(1).reset_index()["Session_Id"]
    artist_list = df[df.Session_Id.isin(session_id)].artistName.unique()
    listToStr = ', '.join([str(elem) for elem in artist_list])
    q.page.add('info_card2', ui.form_card(
    box='1 9 3 2',
    items=[
        ui.text("Your longest session has a total duration of " + str(longest_session_time) + ' minutes.', size='l', width='200px'),
        ui.text('In this session, you listened:  ' + listToStr , size='l', width='200px')
    ]
    ))
    
    #make a top listened artists table
    df_top = df.groupby("artistName").agg({"Minutes":"sum"}).reset_index()
    df_top["Minutes"] = df_top["Minutes"].astype(int)
    df_top = df_top.sort_values("Minutes", ascending=False).head(10)
    n_rows = df_top.shape[0]

    q.page.add('top_artists', ui.form_card(box='10 1 3 6', 
        items=[ ui.table(
        name='Top Artists',
        columns=[ui.table_column(name=str(x), label=str(x), sortable=True) for x in df_top.columns.values],
        rows=[ui.table_row(name=str(i), cells=[str(df_top[col].values[i]) for col in df_top.columns.values])
              for i in range(n_rows)]
        )]
    ))

    #make a top listened songs table
    df_top_songs = df.groupby(["trackName","artistName"]).agg({"Minutes":"count"}).reset_index()
    df_top_songs = df_top_songs.rename(columns= {'trackName':'trackName', 'artistName':'artistName', 'Minutes':'Count'})
    df_top_songs = df_top_songs.sort_values("Count", ascending=False).head(5)
    n_rows = df_top_songs.shape[0]

    q.page.add('top_songs', ui.form_card(box='4 7 4 4', 
        items=[ ui.table(
        name='Top Listened Songs',
        columns=[ui.table_column(name=str(x), label=str(x), sortable=True) for x in df_top_songs.columns.values],
        rows=[ui.table_row(name=str(i), cells=[str(df_top_songs[col].values[i]) for col in df_top_songs.columns.values])
              for i in range(n_rows)]
        )]
    ))

    await q.page.save()