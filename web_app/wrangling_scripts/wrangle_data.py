import datetime as dt
#import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import os
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import time

#* -- Mapping example -----
'''    
    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2014_us_cities.csv')
    df.head()

    df['text'] = df['name'] + '<br>Population ' + (df['pop']/1e6).astype(str)+' million'
    limits = [(0,2),(3,10),(11,20),(21,50),(50,3000)]
    colors = ["royalblue","crimson","lightseagreen","orange","lightgrey"]
    cities = []
    scale = 5000

    fig = go.Figure()

    for i in range(len(limits)):
        lim = limits[i]
        df_sub = df[lim[0]:lim[1]]
        fig.add_trace(go.Scattergeo(
            locationmode = 'USA-states',
            lon = df_sub['lon'],
            lat = df_sub['lat'],
            text = df_sub['text'],
            marker = dict(
                size = df_sub['pop']/scale,
                color = colors[i],
                line_color='rgb(40,40,40)',
                line_width=0.5,
                sizemode = 'area'
            ),
            name = '{0} - {1}'.format(lim[0],lim[1])))

    fig.update_layout(
            title_text = '2014 US city populations<br>(Click legend to toggle traces)',
            showlegend = True,
            geo = dict(
                scope = 'usa',
                landcolor = 'rgb(217, 217, 217)',
            )
        )

    fig.show()



    # base map example
    fig = go.Figure(go.Scattergeo())
    #fig.update_layout(height=300, margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(
            geo = dict(
                scope = 'asia',
                showcountries=True,
                landcolor = 'rgb(217, 217, 217)',
            )
        )
    fig.show()
'''

#! CHECK BEFORE DEPLOYING TO HEROKU !#
#TODO: chg relative file paths to 'data/fname.csv' instead of '../data/fname.csv' for Heroku
#TODO: also check myapp.py has commented out app.run(host='0.0.0.0', port=3001, debug=True)


# just have to save timestamp to_csv instead of os.path.getmtime?
# I don't think can save files to Heroku anyway....need to use sqlite and append updates?
def scrape_tables():
    #fname = '../data/Confirmed.csv'  # only this path works....
    fname = 'data/Confirmed.csv'  # only this path works....
    last_update = os.path.getmtime(fname)
    if time.time() - last_update > (3600 * 2):
        for name in ['Confirmed', 'Deaths', 'Recovered']:
            git_link = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-'+name+'.csv'
            df = pd.read_html(git_link)[0]
            df.to_csv(fname[:5]+name+'.csv')


def cum_data(dataset, china=False):
    ''' Read in csv file from github repo and cleans for plotting

        Args:
        - dataset (str):   data url name: 'Confirmed', 'Deaths', 'Recovered'

        Returns: (df) cleaned dataframe for plotting
    '''
    scrape_tables()
    fpath = 'data/'   # 
    #fpath = '../data/'
    df = pd.read_csv(fpath+dataset+'.csv')

    # try pulling data only from link
    #git_link = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-'+dataset+'.csv'
    #df = pd.read_html(git_link)[0]
    dropcols = [i for i in df.columns if 'Unnamed' in i or 'Lat' in i or 'Lon' in i]
    df = df.drop(dropcols, axis=1)

    if china:
        df = df[df['Country/Region'] == 'Mainland China']
        df = df.set_index('Province/State', drop=True).drop('Country/Region', axis=1)
        df = df.T.fillna(method='ffill')  # make sure most recent date not missing any values
        df.index = pd.to_datetime(df.index)
        df = df.resample('D').max()
        df = df.sum(axis=1)

    else:
        df1 = df['Country/Region'].to_frame()
        df2 = df.iloc[:, 2: ].fillna(method='ffill', axis=1)  # make sure most recent date not missing any values
        df = pd.concat([df1, df2], axis=1)
        df = df.groupby('Country/Region').sum().T
        df.index = pd.DatetimeIndex(df.index)  #.date   # .date gets rid of time portion
        df = df.drop('Mainland China', axis=1)
        df = df.sort_index(axis=1)
        df = df.resample('D').max()
        df = df.sum(axis=1)

    return df


def sars_data(dataset, china=False):
    ''' Gets pre-cleaned SARS csv's

        Args:
        - dataset (str): 'Sars_cases', 'Sars_deaths' or 'Sars_recovered'

        Returns: df
    '''

    #fpath = '../data/'  # use for local
    fpath = 'data/'    # use for Heroku deployment
    df = pd.read_csv(fpath+dataset+'.csv', index_col=0)

    if china:
        df = df.loc['China', : ]
    else:
        df = df.loc['Total', : ] - df.loc['China', : ]

    return df


# Global plotting variables
text_color = 'rgb(200,205,208)'
font_family = 'helvetica'   #family=font_family, 
chart_ht = 320
chart_wth = 420


def plot_cum_stats(china=False, sars=False, scale='linear'):
    ''' Plots cumulative figures
    '''
    #* get data
    if sars:
        confirmed = sars_data('Sars_cases', china=china)
        deaths = sars_data('Sars_deaths', china=china)
        recovered = sars_data('Sars_recovered', china=china)
    else:
        confirmed = cum_data('Confirmed', china=china)
        deaths = cum_data('Deaths', china=china)
        recovered = cum_data('Recovered', china=china)

    #* Create figure with secondary y-axis; custom legend position; opacity control
    if scale == 'log':
        second_y = False
        title = 'Log Scale'
    else: 
        second_y = True
        title = 'Linear Scale'
    
    fig = make_subplots(specs=[[{"secondary_y": second_y}]])
        
    # Add traces
    fig.add_trace(
        go.Bar(
            x=confirmed.index.tolist(), 
            y=confirmed.tolist(),
            marker_color='gray',
            marker_line_width=0,
            #opacity=0.5, 
            name="Cases"), 
            secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=deaths.index.tolist(), 
            y=deaths.tolist(), 
            mode='lines+markers',
            line=dict(color='red', width=1),
            name="Deaths"),
            secondary_y=second_y
    )

    fig.add_trace(
        go.Scatter(
            x=recovered.index.tolist(), 
            y=recovered.tolist(),
            mode='lines+markers',
            line=dict(color='yellow', width=1),
            name="Recoveries"),
            secondary_y=second_y
    )

    # Add figure title
    if china:
        place = 'China'
    else:
        place = 'Rest of World'

    fig.update_layout(
        title={
            'text': '<b>'+place+': '+title+'</b>',
            'x': 0,
            'y': 0.95,
            'xanchor': 'left',
            'yanchor': 'bottom'
        },
        font=dict(size=11, color=text_color),
        legend=dict(x=0.025, y=-0.12, orientation='h', font=dict(size=9)), # bgcolor=None, font=dict(size=12)),  did nothing
        yaxis_type=scale,
        autosize=False,
        width=chart_wth,
        height=chart_ht,
        margin=dict(l=10, r=10, b=5, t=30, pad=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    # Set axis titles
    fig.update_xaxes(tickfont=dict(size=9, color=text_color))
    if scale == 'log':
        fig.update_yaxes(
            title_text="Log Scale", 
            secondary_y=False, 
            title_font=dict(size=11, color=text_color), 
            tickfont=dict(size=9, color=text_color),
            showgrid=False, zeroline=False,
            showline=True, linewidth=2, linecolor='gray'
        )
    else:
        fig.update_yaxes(
            title_text="# Cases", 
            secondary_y=False, 
            title_font=dict(size=11, color=text_color), 
            tickfont=dict(size=9, color=text_color),
            showgrid=False, zeroline=False,
            showline=True, linewidth=2, linecolor='gray'
        )
        fig.update_yaxes(
            title_text="# Deaths/Recoveries", 
            secondary_y=True, 
            title_font=dict(size=11, color=text_color), 
            tickfont=dict(size=9, color=text_color),
            showgrid=False, zeroline=False,
            showline=True, linewidth=2, linecolor='gray'
        )

    return fig


def plot_daily_stats(china=False, sars=False):
    #* get data
    if sars:
        confirmed = sars_data('Sars_cases', china=china)
        deaths = sars_data('Sars_deaths', china=china)
        recovered = sars_data('Sars_recovered', china=china)
    else:
        confirmed = cum_data('Confirmed', china=china)
        deaths = cum_data('Deaths', china=china)
        recovered = cum_data('Recovered', china=china)

    #* calc daily change
    chg_confirmed = confirmed.diff()
    chg_deaths = deaths.diff()
    chg_recovered = recovered.diff()

    #* calc fatality rate
    fatality = deaths / confirmed *100

    #* Create figure with secondary y-axis; custom legend position; opacity control
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(
            x=chg_confirmed.index.tolist(), 
            y=chg_confirmed.tolist(),
            marker_color='gray',
            marker_line_width=0,
            name="Daily Cases"),
            secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=chg_deaths.index.tolist(), 
            y=chg_deaths.tolist(), 
            marker_color='red',
            marker_line_width=0,
            name="Daily Deaths"),
            secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=chg_recovered.index.tolist(), 
            y=chg_recovered.tolist(), 
            marker_color='yellow',
            marker_line_width=0,
            name="Daily Recoveries"),
            secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=fatality.index.tolist(), 
            y=fatality.tolist(), 
            mode='lines+markers',
            line=dict(color='firebrick', width=1),
            name="Fatality Rate (%)"),
            secondary_y=True,
    )

    # Add figure title
    if china:
        place = 'China'
    else:
        place = 'Rest of World'

    fig.update_layout(
        title={
            'text': '<b>'+place+': Daily Chg and Fatality Rate</b>',
            'x': 0,
            'y': 0.95,
            'xanchor': 'left',
            'yanchor': 'bottom',
        },
        font=dict(size=11, color=text_color),
        legend=dict(x=0.025, y=-0.12, orientation='h', font=dict(size=9, color=text_color)),
        barmode='group',
        bargap=0, # gap between bars of adjacent location coordinates.
        bargroupgap=0, # gap between bars of the same location coordinate.
        autosize=False,
        width=chart_wth,
        height=chart_ht,
        margin=dict(l=10, r=10, b=5, t=30, pad=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Set axis titles
    fig.update_xaxes(tickfont=dict(size=9, color=text_color))
    fig.update_yaxes(
        title_text="# Cases", 
        secondary_y=False, 
        title_font=dict(size=11, color=text_color), 
        tickfont=dict(size=9, color=text_color),
        showgrid=False, zeroline=False,
        showline=True, linewidth=2, linecolor='gray'
    )
    fig.update_yaxes(
        title_text="Fatality Rate (%)", 
        secondary_y=True, 
        title_font=dict(size=11, color=text_color), 
        tickfont=dict(size=9, color=text_color),
        showgrid=False, zeroline=False,
        showline=True, linewidth=2, linecolor='gray'
    )
    return fig


def return_figures():
    # append all charts to the figures list
    figures = []
    # Carona figs
    figures.append(plot_cum_stats(china=True, scale='linear'))
    figures.append(plot_cum_stats(china=True, scale='log'))
    figures.append(plot_daily_stats(china=True))
    figures.append(plot_cum_stats(scale='linear'))
    figures.append(plot_cum_stats(scale='log'))
    figures.append(plot_daily_stats())
    # SARS figs
    figures.append(plot_cum_stats(china=True, sars=True, scale='linear'))
    figures.append(plot_cum_stats(china=True, sars=True, scale='log'))
    figures.append(plot_daily_stats(china=True, sars=True))
    figures.append(plot_cum_stats(sars=True, scale='linear'))
    figures.append(plot_cum_stats(sars=True, scale='log'))
    figures.append(plot_daily_stats(sars=True))

    return figures



