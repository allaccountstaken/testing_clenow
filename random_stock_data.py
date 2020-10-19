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
    
    