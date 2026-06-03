This is a fun project I've embarked on where the goal is to implement my trading strategy into a Python script and have that strategy present itself on the chart of my choice. I will initially look to just chart the strategy and set up alerts for when trade entries should occur, but in the future I will look to automate the actual trading part.

Here is the goal of this project:
1. Use the Interactive Brokers' (quite robust) API to interact with the financial markets and acquire commodity data.
2. Display that data on a bar graph developed with TradingView's Lightweight Charts API.
3. Translate my trading strategy into code
4. Feed the financial data gathered from IB's API to my strategy's code, and portray my strategy onto any given chart

Requirements:
- Python IDE
- Interactive Brokers TWS App: ([link](https://www.interactivebrokers.com/en/trading/download-tws.php?p=stable))
- APIs for IB and Lightweight Charts are already in the files




References:
- https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc
- https://www.interactivebrokers.com/campus/ibkr-quant-news/interactive-brokers-python-api-native-a-step-by-step-guide/



P.S.
going to take a break from this project for now and focus on another one for the time being which is a backtesting project. here, I can fine-tune my strategy and backtest it with years of historical data. will work on that for the time being and come back to this project once I've got the python code set up for my strategy implementation.
