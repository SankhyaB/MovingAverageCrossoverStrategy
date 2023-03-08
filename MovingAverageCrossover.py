"""
- Considering Ethereum markets but can be applied to any market including indexes
- Information dated between December 1st 2019 - December 1st 2022 (Three years of historical data)
- Mapping out 10 and 50 day moving averages
- 5 ATR - Selling Price with a -1 ATR trailing stop loss
"""

# importing necessary packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math


def calculating_returns(prices):
    # Considering one share bought
    buying_price = 0
    selling_price = 0
    total_returns = 0
    for rows in prices.iterrows():
        buying_price = buying_price + rows[1][0]
        selling_price = selling_price + rows[1][1]
    return ((selling_price - buying_price) / buying_price) * 100


def closest_value(input_list, input_value):
    i = 0
    arr = np.asarray(input_list)
    if arr.size:
        i = (np.abs(arr - input_value)).argmin()
    return arr[i]


# Finding the close prices closest to the ATR values with magnitude 5 and -1
def incorporating_atr(data, atr):
    # The new dataframe we are returning
    df2 = pd.DataFrame()
    atr = atr.to_frame()
    atr.columns = {'ATR_Values'}
    example = pd.merge(data, atr, on='Date')
    # Now example has Close Values and ATR Values together
    dog = example[example['Close_Pattern'] != 0]
    dog = dog.loc[:, dog.columns.drop(['20_SMA', '50_SMA', 'Pattern', 'Position', 'New_Pattern', 'Close_Pattern'])]
    dog['5Mag'] = dog['Close'] + 5 * dog['ATR_Values']
    dog['-1Mag'] = dog['Close'] + (-1 * dog['ATR_Values'])
    # The dog dataframe has information of all the positions considered and their respective 5Mag and
    # -1Mag positions

    for index_one, row_set1 in dog.iterrows():
        flag = 0
        second_flag = 0
        newList = []
        for index_two, row_set2 in data.iterrows():

            if (index_one == index_two) | (flag == 1):
                if math.isclose(row_set2['Close'], row_set1['5Mag'], abs_tol=50):
                    newList.append(row_set2['Close'])
                flag = 1

        if len(newList) == 0:
            for index_two_2, row_set2_2 in data.iterrows():
                if (index_one == index_two_2) | (second_flag == 1):
                    if math.isclose(row_set2_2['Close'], row_set1['-1Mag'], abs_tol=50):
                        newList.append(row_set2_2['Close'])
                    second_flag = 1
        if second_flag == 1:
            df1 = pd.DataFrame({"Purchasing_Price": [row_set1['Close']],
                                "Selling_Price": [closest_value(newList, row_set1['-1Mag'])],
                                "Closest_Price_to_ATR": [row_set1['-1Mag']]})
        else:
            df1 = pd.DataFrame({"Purchasing_Price": [row_set1['Close']],
                                "Selling_Price": [closest_value(newList, row_set1['-1Mag'])],
                                "Closest_Price_to_ATR": [row_set1['5Mag']]})
        df2 = pd.concat([df2, df1])
    return df2


# Market Prices, Moving Averages, Buying Points(marked with ^ green points)
def graphing_positions(data):
    """
    Plot the close price, 20-MA and 50-MA graphs
    When there are buy and sell signals, you mark arrows and display them
    :param data: df2 that contains Date, Close, 20_SMA, 50_SMA, Pattern, Position
    :return: Graph that shows all the graphing positions
    """

    data['New_Pattern'] = np.where(data['Position'] == 1, 1, 0)
    data['Close_Pattern'] = np.where(data['Position'] == 1, data['Close'], 0)

    plt.scatter(data.index, data['Close_Pattern'], marker='^', color='green', label="Buy", s=100)
    data['Close'].plot(label="Stock Price")
    data['20_SMA'].plot(label="20-Day MA")
    data['50_SMA'].plot(label="50-Day MA")
    """
    This plot demonstrates the Close Price, the moving averages for 20 day and 50 day as well as buying stock price
    positions when there is a positive crossover
    """
    plt.ylabel("Market Price")
    plt.xlabel("Date(Past 3 years)")
    plt.title("Stock Price - MA Crossover")
    plt.legend()
    # plt.show()

    return data


# Marks the information of the 20_SMA and the 50_SMA
def newDataFrameAndMA(data):
    df2 = data.loc[:, data.columns.drop(['Open', 'High', 'Low', 'Volume', 'Adj Close'])]
    # we have a new data frame now with the Date as index and close prices as a column

    df2['20_SMA'] = df2['Close'].rolling(window=20, min_periods=1).mean()
    df2['50_SMA'] = df2['Close'].rolling(window=50, min_periods=1).mean()
    
    # moving_average_plotting(data, df2['50_SMA'], df2['20_SMA'])

    # Looking into exponential moving averages
    # df2['20_SMA'] = df2['Close'].ewm(span=20, adjust=False).mean()
    # df2['50_SMA'] = df2['Close'].ewm(span=50, adjust=False).mean()
    
    """Now we can add the position columns:
       - A "Pattern" parameter is 0.0 by default
           - When the 20 day MA is greater than the 50 day MA, the "Pattern" is set to 1
           - When the 20 day MA is lesser than the 50 day MA, the "Pattern" is set to 0
       - A "Position" Parameter is calculated using the difference of the "Pattern"
           - When the "Position" is 1, it implies that the pattern changed from 0 to 1 - buy call
           - When the "Position" is -1, it implies that the pattern changed from 1 to 0 - sell call
       - Technically you are only dealing with a single security 
    """
    df2['Pattern'] = 0
    df2['Pattern'] = np.where(df2['20_SMA'] > df2['50_SMA'], 1, 0)
    df2['Position'] = df2['Pattern'].diff()
    # graphing_positions(df2)
    return df2


# ATR values that are given to this specific variable
def calculating_ATR(data):
    """
    Calculate high-low, high-close, low-close
    Find the maximum of the three, and return rolling values based on the previous 14 days
    :param data: historical financial information
    :return: pandas.core.Series.series ATR values
    """
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    potential_ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(potential_ranges, axis=1)
    fresh_ATR = (true_range.rolling(14).sum() / 14).iloc[13:]
    fresh_ATR.reset_index(drop=True)
    return fresh_ATR


# plot the ATR content along with the financial data 
def plotting_setup(data, atr):
    fig, ax = plt.subplots()
    atr.plot(ax=ax, label='ATR-Values')
    data['Close'].plot(ax=ax, secondary_y=True, alpha=0.3, label='Stock Price' )
    plt.ylabel("Market Price")
    plt.xlabel("Date(Past 3 years)")
    plt.title("ATR Values-Stock Price Crossover")
    plt.legend()
    # plt.show()
    plt.show()


# Plots the moving averages against the particular stock price - 50-day MA is the smoother of the two
# Method call made from newDataFrameAndMA()
def moving_average_plotting(data, SMA_50, SMA_20):
    fig, ax = plt.subplots()
    data['Close'].plot(ax=ax, secondary_y=True, alpha=0.3)
    SMA_20.plot(ax=ax)
    SMA_50.plot(ax=ax)
    plt.show()


# Modifies the information to take into account the unavailability of the ATR for the first 13 days
def iloc_method(data):
    return data.iloc[13:]


def main(ETH_CSV):

    # Since the ATR is not available for the first 13 days, we modify the dates to start from December 14th 2020
    new_csv = iloc_method(ETH_CSV)

    # Marks the patterns and the positions
    improved_data = newDataFrameAndMA(new_csv)
    
    # Market Prices, Moving Averages, Buying Points(marked with ^ green points)
    graphing_positions(improved_data)
    
    # ATR values that are given to this specific variable
    atr_content = calculating_ATR(ETH_CSV)
    
    # plot the ATR content
    plotting_setup(new_csv, atr_content)
    
    # Plot the graph with the stock price information, moving average information and buying positions
    new_improved_data = graphing_positions(improved_data)
    
    # Finding the close prices closest to the ATR values with magnitude 5 and -1
    prices = incorporating_atr(new_improved_data, atr_content)
    
    # Calculating the total net returns of from the past three years for the SMA Crossover strategy - only buy calls
    print("Total Returns(only buy positions): ", calculating_returns(prices))


if __name__ == "__main__":
    """Reading from the CSV file, setting the index to the date and calling main
       Dates: 14th December 2020 - December 1st 2022"""
    ETH_CSV = pd.read_csv('ETH.csv')
    ETH_CSV.set_index('Date', inplace=True)
    main(ETH_CSV)
