from datetime import date

def get_current_month_and_year():
    dict = {
        "Year" : '',
        "Month" : '',
        "Day" : ''
    }
    today = date.today().strftime("%Y-%B-%d").split('-')

    dict['Year'] = today[0]
    dict['Month'] = today[1]
    dict['Day'] = today[2]

    return dict

if __name__ == "__main__":
    print('getting date in main file..\n')
    todays_date = get_current_month_and_year()

    current_year = todays_date['Year']
    current_month = todays_date['Month']
    current_day = todays_date['Day']

    print(f"{current_year = }")
    print(f"{current_month = }")
    print(f"{current_day = }")
