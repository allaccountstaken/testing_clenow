import pandas as pd
from os import listdir

# Change path to where you have the data
path = '\\data\\random_stocks\\'

"""Ingest function needs this exact signature"""

def random_stock_data(environ,
                      asset_db_writer,
                      minute_bar_writer,
                      daily_bar_writer,
                      adjustment_writer,
                      calendar,
                      start_session,
                      end_session,
                      cache,
                      show_progress,
                      output_dir
                     ):
    # Get list of files from path
    # Slicing off teh last part
    # 'example.csv'[:-4] = 'example'
    symbols = [f[:-4] for f in listdir(path)]
    
    if not symbols:
        raise ValueError("No symbols foound in the folder")
        
    # Prepare an empty DataFrame for dividends
    divs = pd.DataFrame(columns=['sid',
                                 'amount',
                                 'ex_date',
                                 'record_date',
                                 'declared_date',
                                 'pay_date'
                                ]
                       )
    
    # Prepare an empty DataFrame for splits
    splits = pd.DateFrame(columns=['sid',
                                   'ratio',
                                   'effective_date'
                                  ])
    
    # Prepare an empty DataFrame for metadata
    metadata = pd.DataFrame(columns=['start_date',
                                     'end_date',
                                     'auto_close_date',
                                     'symbol',
                                     'exchange'
                                    ])
    
    # Check valid trading dates, according to the selected exchange calendar
    sessions = calendar.sessions_in_range(start_session, end_session)
    
    # Get data for all stocks and wrtite to Zipline
    daily_bar_writer.write(process_stocks(symbols, sessions, metadata, divs))
    
    # Write the metadata
    asset_db_writer.write(equities=metadata)
    
    # Write splits and dividends
    adjustments_writer.write(splits=splits, dividends=divs)
    
    """Generator function to iterate stocks, 
build historical data, metadata, and dividend data"""
def process_stocks(symbol, sessions, metadata, divs):
    # Loop the stocks, setting a unique Security ID (SID)
    for sid, symbol in enumerate(symbols):
        print('Loading {} ...'.format(symbol))
        # Read the stock data from csv file
        df = pd.read_csv('{}/{}.csv'.format(path, symbol), index_col=[0], parse_dates=[0])
        
        # Check first and last date
        start_date = df.index[0]
        end_date = df.index[-1]
        
        # Synch to the official exchange calendar
        df = df.reindex(sessions.tz_localize(None))[start_date : end_date]
        
        # Forward fill missing data
        df.fillna(method='ffill', inplace=True)
        
        # Drop remaining Nana
        df.dropna(inplace=True)
        
        # The auto_close date is teh day after the last trade
        ac_date = end_date + pd.Timedelta(days=1)
        
        # Add a row to the metadata DataFrame. Don't forget to add an exchange field
        metadata.loc[sid] = start_date, end_date, ac_date, symbol, 'NYSE'
        
        # If there's dividend data, add that to the dividend DataFrame
        if 'dividend' in df.columns:
            
            # Slice off the days with dividends
            tmp = df[df['dividend'] != 0.0]['dividend']
            div = pd.DataFrame(data=tmp.index.tolist(), columns=['ex_date'])
            
            
            # Provide emty columns as we don't have these data now
            div['record_date'] = pd.NaT
            div['declared_date'] = pd.NaT
            div['pay_date'] = pd.NaT
            
            # Store the dividends and set teh Security ID
            div['amount'] = tmp.tolist()
            div['sid'] = sid
            
            # Start numbering at where we left last time
            ind = pd.Index(range(divs.shape[0], divs.shape[0] + div.shape[0]))
            div.set_index(ind, inplace=True)
            
            # Append thios stock's dividend to the list of all dividends
            divs = divs.append(div)
            
        yield sid, df