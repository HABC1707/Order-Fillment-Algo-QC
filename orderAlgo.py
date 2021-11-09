class AdaptableSkyBlueLlama(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2018, 1, 1)  
        self.SetEndDate(2021, 11, 10)
        self.SetCash(100000)
        
        self.qqq = self.AddEquity("QQQ", Resolution.Hour).Symbol
        
        self.entry_ticket = None
        self.stop_market_ticket = None
        self.entry_time = datetime.min
        self.stop_market_order_fill_time = datetime.min
        self.highest_price = 0
        
        
    def OnData(self, data):
        
        # Wait 30 days after last exit
        if (self.Time - self.stop_market_order_fill_time).days < 30:
            return
        
        price = self.Securities[self.qqq].Price
        
        # Send Entry Limit Order
        if not self.Portfolio.Invested and not self.Transactions.GetOpenOrders(self.qqq):
            quantity = self.CalculateOrderQuantity(self.qqq, .9)
            self.entry_ticket = self.LimitOrder(self.qqq, quantity, price, "Entry Order")
            self.entry_time = self.Time
        
        # Move Limit price if not filled after 1 day
        if (self.Time - self.entry_time).days > 1 and self.entry_ticket.Status != OrderStatus.Filled:
            self.entry_time = self.Time
            updateFields = UpdateOrderFields()
            updateFields.LimitPrice = price
            self.entry_ticket.Update(updateFields)
        
        # Move up trailing stop price
        if self.stop_market_ticket is not None and self.Portfolio.Invested:
            if price > self.highest_price:
                self.highest_price = price
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = price * .95
                self.stop_market_ticket.Update(updateFields)
                
    
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status != OrderStatus.Filled:
            return
        
        # Send Stop Loss Order if Entry Limit Order is filled
        if self.entry_ticket is not None and self.entry_ticket.OrderId == orderEvent.OrderId:
            self.stop_market_ticket = self.StopMarketOrder(self.qqq, -self.entry_ticket.Quantity,
                                                           .95 * self.entry_ticket.AverageFillPrice)
        
        # Save Fill Time of Stop Loss Order
        if self.stop_market_ticket is not None and self.stop_market_ticket.OrderId == orderEvent.OrderId:
            self.stop_market_order_fill_time = self.Time
            self.highestPrice = 0
