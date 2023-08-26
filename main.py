from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedStyle
import time
import gspread
import pandas as pd


#Journal Updater , Trends

sa = gspread.service_account(filename='service_account.json')

sheets = sa.open('TradesList')

journal = sheets.worksheet('Journal')

def ConvertTrade(sidepos,tf,op,tp,sl,money_at_full_tp,money_at_risk,rr,pos_size,tpperc,slperc,trigger):
    trade = {
        'date_open':'',
        'date_closed':'',
        'side':sidepos,
        'ID':'',
        'instrument':'Nasdaq_futures',
        'tf': tf,
        'open_limit':op,
        'tp_price': tp,
        'sl_price': sl,
        'price_filled': '',
        '$_at_risk': '',
        '$_at_full_tp': money_at_full_tp,
        '$_at_risk': money_at_risk,
        'rr': rr,
        'pos_size': pos_size,
        'lev':'20',
        'tp%': tpperc,
        'sl%': slperc,
        'trigger': trigger,
        'result%': '',
        'result_nominal': '',
        'fee': ''

    }
    return trade


def Add_trade_to_gsheet():
    trade = ConvertTrade(sidepos,tf,op,tp,sl,money_at_full_tp,money_at_risk,rr,size,tpperc,slperc,trigger)
    trade_to_export=[trade['date_open'], 
                     trade['date_closed'],
                     trade['side'],
                     trade['ID'],
                     trade['instrument'],
                     trade['tf'],
                     trade['open_limit'],
                     trade['tp_price'],
                     trade['sl_price'],
                     trade['price_filled'],
                     trade['$_at_risk'],
                     trade['$_at_full_tp'],
                     trade['rr'],
                     trade['pos_size'],
                     trade['lev'],
                     trade['tp%'],
                     trade['sl%'],
                     trade['trigger'],
                     trade['result%'],
                     trade['result_nominal'],
                     trade['fee']
    ]
    try:
        journal.append_row(trade_to_export, table_range="A1:U")
        return True
    except:
        return False


#Trends

global weekly_trend
weekly_trend = 'up'

WoWo = sheets.worksheet('WoWoTrends')
Trends = WoWo.get('A1:F12')
Trendsdf = pd.DataFrame(Trends)
Trendsdf.columns=Trendsdf.iloc[0]
Trendsdf = Trendsdf.tail(-1)



#functionality part

##trade vars

global op
global sl
global tp
global size
global trigger
global tf
global sidepos
global money_at_full_tp
global money_at_risk
global rr
global tpperc
global slperc

global ordertype
ordertype = 'limit'


global trade_confirmed
trade_confirmed = False

def assign_globals(op,sl,tp,size,trigger,tf,sidepos,money_at_full_tp,money_at_risk,rr,tpperc,slperc):
    globals()['op'] = op
    globals()['sl'] = sl
    globals()['tp'] = tp
    globals()['size'] = size
    globals()['trigger'] = trigger
    globals()['tf'] = tf
    globals()['sidepos'] = sidepos

    globals()['money_at_full_tp'] = money_at_full_tp
    globals()['money_at_risk'] = money_at_risk
    globals()['rr'] = rr
    globals()['tpperc'] = tpperc
    globals()['slperc'] = slperc


def buy():
    calculate('buy')

def sell():
    calculate('sell')

def send_order(ordtype):
    time.sleep(3)
    textarea.delete('1.0','end')

def setorder():
    textarea.delete('1.0','end')
    if globals()['trade_confirmed'] == False:
        textarea.insert(INSERT,"Position not approved")
    elif globals()['trade_confirmed'] == True:
        globals()['ordertype'] = ordertype_combo.get()
        textarea.insert(INSERT,"Sending the order...")

        if globals()['ordertype'] == 'limit':
            send_order('limit')

        elif globals()['ordertype'] == 'market':
            send_order('market')
        textarea.insert(INSERT,f"{globals()['ordertype']} order successfully sent!")
        try:
            Add_trade_to_gsheet()
            textarea.insert(INSERT,"\nSuccessfully added Trade to the Journal")
        except:
            textarea.insert(INSERT,"\nAdding Trade to the Journal Failed")
        globals()['trade_confirmed'] = False

def calculate(side):
    try:
        textarea.delete('1.0','end')
        op = float(OP_Entry.get())
        sl = float(SL_Entry.get())
        tp = float(TP_Entry.get())
        size = float(Size1.get())
        trigger = Trigger_combo.get()
        tf = TF_combo.get()
        sidepos = side

        if (op == "") or (sl == "") or (tp == "") or (size == "") or (trigger == "") or (tf == ""):
            textarea.insert(INSERT,'Some fields are empty, fill them')
            globals()['trade_confirmed'] = False
        else:  
            if sidepos == 'buy':
                if tp > op and sl < op:
                    tpperc = round((tp - op)/op,2)
                    slperc = round((op - sl)/sl,2)
                    tpnominal = round(tpperc * size,2)
                    slnominal = round(slperc * size,2)
                    rratio = round(tpnominal / slnominal,2)
                    if rratio < 1.5:
                        textarea.insert(INSERT,f"RR is {rratio}, enter values to have at least 1.5 RR")
                        globals()['trade_confirmed'] = False
                    else:
                        if weekly_trend != 'up':
                            if slnominal > 20:
                                textarea.insert(INSERT,f'Too much risk again the weekly trend: -{slnominal} pln')
                                globals()['trade_confirmed'] = False
                                return
                        if slnominal > 100:
                            textarea.insert(INSERT,f"\nYou risk too much, nominal SL is -{slnominal} pln, consider up to -100 pln (0.33%)")
                            globals()['trade_confirmed'] = False
                            return

                        else:
                            globals()['trade_confirmed'] = True
                            textarea.insert(INSERT,f'Long trade confirmed! Click Set order to set a limit order.\nTP: +{tpnominal} pln (+{tpperc*100}%) \nSL: -{slnominal} pln (-{slperc*100}%)\nRR:{rratio}')
                            assign_globals(op,sl,tp,size,trigger,tf,sidepos,tpnominal,slnominal,rratio,tpperc,slperc)
                            
                else:
                    textarea.insert(INSERT,'Incorrect TP / SL, correct them')
                    globals()['trade_confirmed'] = False

            elif sidepos == 'sell':
                
                if tp < op and sl > op:
                    tpperc = round((op - tp)/op,2)
                    slperc = round((sl - op)/sl,2)
                    tpnominal = round(tpperc * size,2)
                    slnominal = round(slperc * size,2)
                    rratio = round(tpnominal / slnominal,2)
                    if rratio < 1.5:
                        textarea.insert(INSERT,f"RR is {rratio}, enter values to have at least 1.5 RR")
                        globals()['trade_confirmed'] = False
                    else:
                        if weekly_trend != 'down':
                            if slnominal > 25:
                                textarea.insert(INSERT,f'Too much risk again the weekly trend: -{slnominal} pln')
                                globals()['trade_confirmed'] = False
                                return
                        if slnominal > 100:
                            textarea.insert(INSERT,f"\nYou risk too much, nominal SL is -{slnominal} pln, consider up to -100 pln (0.33%)")
                            globals()['trade_confirmed'] = False

                        else:
                            
                            globals()['trade_confirmed'] = True
                            textarea.insert(INSERT,f'Short trade confirmed! Click Set order to set a limit order.\nTP: +{tpnominal} pln (+{tpperc*100}%) \nSL: -{slnominal} pln (-{slperc*100}%)\nRR:{rratio}')
                            assign_globals(op,sl,tp,size,trigger,tf,sidepos,tpnominal,slnominal,rratio,tpperc,slperc)
                            

                else:
                    textarea.insert(INSERT,'Incorrect TP / SL, correct them')
                    globals()['trade_confirmed'] = False

    except ValueError:
        textarea.delete('1.0','end')
        textarea.insert(INSERT,'Calculation error, correct the numbers')
        globals()['trade_confirmed'] = False



#GUI part

root = Tk()

root.title('Trading Service Manager')
root.geometry('1920x1080')
root.iconbitmap('logot.ico')

headingLabel=Label(root,text='Trading Service Manager',font=('arial',20,'bold')
                   ,bg='CadetBlue2',fg='blue4',bd=12,relief=FLAT)
headingLabel.pack(fill=X)

trading_setup_frame=LabelFrame(root,text='Trade Setup',font=('arial',15,'bold'),
                               fg='blue4',border=8,relief=GROOVE,bg='CadetBlue2',pady=5)
trading_setup_frame.pack(fill=X)

padxvar = 8
padyvar = 4

OP_label=Label(trading_setup_frame,text='Open Price',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
OP_label.grid(row=0,column=0,padx=padxvar,pady=2)

OP_Entry = Entry(trading_setup_frame,font=('arial',15,'normal'),bd=2,width=8)
OP_Entry.grid(row=0,column=1,padx=padxvar)

SL_label=Label(trading_setup_frame,text='SL Price',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
SL_label.grid(row=0,column=2,padx=padxvar,pady=2)

SL_Entry = Entry(trading_setup_frame,font=('arial',15,'normal'),bd=2,width=8)
SL_Entry.grid(row=0,column=3,padx=padxvar)

TP_label=Label(trading_setup_frame,text='TP Price',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
TP_label.grid(row=0,column=4,padx=padxvar,pady=2)

TP_Entry = Entry(trading_setup_frame,font=('arial',15,'normal'),bd=2,width=8)
TP_Entry.grid(row=0,column=5,padx=padxvar)

Size_label=Label(trading_setup_frame,text='POS size',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
Size_label.grid(row=0,column=6,padx=padxvar,pady=2)

Size1 = Entry(trading_setup_frame,font=('arial',15,'normal'),bd=2,width=8)
Size1.grid(row=0,column=7,padx=padxvar)

Trigger_label=Label(trading_setup_frame,text='Trigger',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
Trigger_label.grid(row=0,column=8,padx=padxvar,pady=2)

Trigger_combo = ttk.Combobox(trading_setup_frame,state="readonly",font=('arial',15,'normal'),values=["OB-Reject", "Trend-break", "StrongMove-OppositeBet", "Trend-support"],width=11)
Trigger_combo.grid(row=0,column=9,padx=padxvar)


TF_label=Label(trading_setup_frame,text='TF',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
TF_label.grid(row=0,column=10,padx=padxvar,pady=2)

TF_combo = ttk.Combobox(trading_setup_frame,state="readonly",font=('arial',15,'normal'),values=["15m","1h","4h","1d","5m","1m","1w"],width=4)
TF_combo.grid(row=0,column=11,padx=padxvar)

ordertype_label=Label(trading_setup_frame,text='type',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue2')
ordertype_label.grid(row=0,column=12,padx=padxvar,pady=2)

ordertype_combo = ttk.Combobox(trading_setup_frame,state="readonly",font=('arial',15,'normal'),values=["market"],width=4)
ordertype_combo.current(0)
ordertype_combo.grid(row=0,column=13,padx=padxvar)



#
buttons_frame=LabelFrame(root,text='Actions',font=('arial',15,'bold'),
                               fg='blue4',border=8,relief=GROOVE,bg='CadetBlue2',pady=5)
buttons_frame.pack(fill=X)

buy_button = Button(buttons_frame,text='Buy',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue3',bd=2,command=buy)
buy_button.grid(row=0,column=0,padx=padxvar,pady=padyvar)

sell_button = Button(buttons_frame,text='Sell',font=('arial',15,'normal'),fg='blue4',bg='Cadetblue3',bd=2,command=sell)
sell_button.grid(row=0,column=1,padx=padxvar,pady=padyvar)

set_order_button = Button(buttons_frame,text='Set order',font=('normal',15,'bold'),fg='blue4',bg='Cadetblue3',bd=2,command=setorder)
set_order_button.grid(row=0,column=2,padx=padxvar,pady=padyvar)


output_frame=Frame(buttons_frame,bd=6,relief=GROOVE)
output_frame.grid(row=0,rowspan=1,column=3,padx=25,pady=1)

output_label = Label(output_frame,text='Output',font=('arial',11,'normal'))

output_label.pack()

scrollbar = Scrollbar(output_frame,orient=VERTICAL)
scrollbar.pack(side=RIGHT,fill=Y)
textarea = Text(output_frame,height=4,width=71,padx=15,font=('normal',15,'bold'),bg='blue4',fg='white')
textarea.pack(fill=X)



# Convert Pandas DataFrame to a Tkinter Table (Treeview)

# Apply the "clam" theme from ttkthemes
style = ThemedStyle(root)
style.set_theme("clam")  # You can change the theme here


'''style = ttk.Style()

style.configure("Treeview",
                font=('arial', 15, 'normal'),
                foreground='blue4',
                background='CadetBlue3',
                borderwidth=2)


tree = ttk.Treeview(root,style="Treeview")
'''
tree = ttk.Treeview(root, columns=Trendsdf.columns.tolist(), show="headings")

# tree["columns"] = Trendsdf.columns.tolist()
for col in Trendsdf.columns:
    tree.column(col, anchor="center")
    tree.heading(col, text=col)
    
# Insert data into the treeview
for i, row in Trendsdf.iterrows():
    tree.insert("", "end", values=row.tolist())

# Pack the treeview
tree.pack()


root.mainloop()

