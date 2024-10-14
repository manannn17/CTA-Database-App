# Name: Manan Patel
# UIN: 658283328
# Net ID: mpate360@uic.edu
# CS341 Project-1

import sqlite3 #import files
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Connection in the database
dbConn = sqlite3.connect("CTA2_L_daily_ridership.db")
cursor = dbConn.cursor()


def show_general_statistics():
    #database info
    try:
        cursor.execute('select count(*) from Stations')
        num_stations = cursor.fetchone()[0]  # Fetch the first element of the tuple
    except sqlite3.OperationalError:
        print("Table 'Stations' does not exist.")
        return

    cursor.execute('select count(*) from Stops') #table query for Stops
    num_stops = cursor.fetchone()[0]

    cursor.execute('select count(*) from Ridership') #table query total number of ride entries
    num_rides = cursor.fetchone()[0]

    cursor.execute('select distinct min(Ride_Date), max(Ride_Date) from Ridership')
    min_date, max_date = cursor.fetchone()
    min_date = str(min_date).split(" ")[0]  # for format mm-dd-yyyy
    max_date = str(max_date).split(" ")[0]

    cursor.execute('select sum(Num_Riders) from Ridership')
    total_riders = cursor.fetchone()[0] # query for total number of riders

    # Printing the required output
    print(f"** Welcome to CTA L analysis app **\n")
    print(f"General Statistics:")
    print(f"  # of stations: {num_stations}")
    print(f"  # of stops: {num_stops}")
    print(f"  # of ride entries: {num_rides:,}")
    print(f"  date range: {min_date} - {max_date}")
    print(f"  Total ridership: {total_riders:,}")


def find_station_by_partial_name(partial_name):
    #Command 1
    cursor=dbConn.cursor() # Re-establishing cursor
    # cursor.execute('select Station_ID, Station_Name from Stations where Station_Name '
    #                'like ?', (partial_name,))
    query="select Station_ID, Station_Name from Stations where Station_Name like ? order by Station_Name asc"
    cursor.execute(query,(partial_name,))  #SQL query with a match

    rows = cursor.fetchall() #get all rows

    if not rows:
        print("**No stations found...") #print no if no station found
    else:
        for station_id, station_name in rows: #print stations
            print(f"{station_id} : {station_name}")


def analyze_station_ridership(station_name):
    #Command 2
    cursor=dbConn.cursor()

    cursor.execute('select Station_ID from Stations where Station_Name = ?', (station_name,))
    result = cursor.fetchone()

    if not result:
        print("**No data found...")  # Print if no station found
        return

    station_id = result[0]

    #calculate ridership based on the type
    cursor.execute('''select 
                        SUM(case when Type_of_Day = 'W' then Num_Riders else 0 end),
                        SUM(case when Type_of_Day = 'A' then Num_Riders else 0 end),
                        SUM(case when Type_of_Day = 'U' then Num_Riders else 0 end),
                        SUM(Num_Riders)
                      from Ridership where Station_ID = ?''', (station_id,))
    weekday_riders, saturday_riders, sunday_riders, total_riders = cursor.fetchone()

    if total_riders == 0:
        print("**No data found...")
        return

    weekday_pct = (weekday_riders / total_riders) * 100  # Calculate percentage ridership for weekdays, Saturdays, and Sundays
    saturday_pct = (saturday_riders / total_riders) * 100
    sunday_pct = (sunday_riders / total_riders) * 100

    # Print ridership
    print(f"Percentage of ridership for the {station_name} station:")
    print(f"  Weekday ridership: {weekday_riders:,} ({weekday_pct:.2f}%)")
    print(f"  Saturday ridership: {saturday_riders:,} ({saturday_pct:.2f}%)")
    print(f"  Sunday/holiday ridership: {sunday_riders:,} ({sunday_pct:.2f}%)")
    print(f"  Total ridership: {total_riders:,}")


def ridership_on_weekdays():
    #Command 3
    cursor = dbConn.cursor()

    #query to get total weekday ridership per station
    query="""select Stations.Station_Name, sum(Num_Riders) as Total_Weekday_Riders
                          from Ridership
                          join Stations on Ridership.Station_ID = Stations.Station_ID
                          where Type_of_Day = 'W'
                          group by Stations.Station_Name
                          order by Total_Weekday_Riders desc;"""

    cursor.execute(query)
    rows = cursor.fetchall()
    total_weekday_riders = sum([row for _, row in rows])

    # Print the ridership data
    print("Ridership on Weekdays for Each Station")
    for station_name, total_riders in rows:
        #station_name, total_riders = row
        percentage = (total_riders / total_weekday_riders) * 100
        print(f"{station_name} : {total_riders:,} ({percentage:.2f}%)")


def stops_by_line_and_direction(dbConn):
    #Command 4

    cursor = dbConn.cursor()

    line_color=input("\nEnter a line color (e.g. Red or Yellow): ")  #user input
    cursor.execute('select Line_ID from Lines where upper(Color) = upper(?)', (line_color,))
    line_data = cursor.fetchone()

    if not line_data:
        print("**No such line...")
        return

    direction = input("Enter a direction (N/S/W/E): ")

    # query for the line runs in the given direction
    cursor.execute("""select distinct Stops.Direction
                          from Stops
                          join StopDetails on Stops.Stop_ID = StopDetails.Stop_ID
                          join Lines on StopDetails.Line_ID = Lines.Line_ID
                          where upper(Lines.Color)=upper(?) and upper(Stops.Direction)=upper(?);""",
                   (line_color, direction))
    rows = cursor.fetchall()

    if not rows:
        print("**That line does not run in the direction chosen...") # Print if no matching direction found
        return

    # Fetch stops with ADA information
    cursor.execute('''select Stops.Stop_Name, Stops.Direction, Stops.ADA
                          from Stops
                          join StopDetails on Stops.Stop_ID = StopDetails.Stop_ID
                          join Lines on StopDetails.Line_ID = Lines.Line_ID
                          where upper(Lines.Color)=upper(?) and upper(Stops.Direction)=upper(?)
                          order by Stops.Stop_Name''', (line_color, direction))
    rows = cursor.fetchall()

    if not rows:
        print("**No stops found for this line and direction...")
        return

    for stop_name, stop_direction, is_ada in rows:
        ada_status = "(handicap accessible)" if is_ada else "(not handicap accessible)"
        print(f"{stop_name} : direction = {stop_direction} {ada_status}")

def stops_by_line_and_direction_with_percentage():
    # Command 5
    #Output the number of stops for each line color, separated by direction
    cursor.execute('''
        select L.Color, S.Direction, count(S.Stop_ID) as num_stops
        from Stops S
        join StopDetails SD on S.Stop_ID = SD.Stop_ID
        join Lines L ON SD.Line_ID = L.Line_ID
        group by L.Color, S.Direction
        order by L.Color asc, S.Direction asc
    ''')

    rows = cursor.fetchall()

    # Get the total number of stops to calculate percentages
    cursor.execute('select count(*) from Stops')
    total_stops = cursor.fetchone()[0]

    if not rows:
        print("**No stops found...")
        return

    print("Number of Stops For Each Color By Direction")

    # Display the results with percentage
    for row in rows:
        color, direction, num_stops = row
        percentage = (num_stops / total_stops) * 100
        print(f"{color} going {direction} : {num_stops} ({percentage:.2f}%)")


def yearly_ridership_by_station(dbConn):
    #Command 6

    cursor = dbConn.cursor()
    station_name = input("\nEnter a station name (wildcards _ and %): ") #user input
    cursor.execute('select distinct Station_Name from Stations where Station_Name like ?', (station_name,))
    station_id = cursor.fetchall()

    if len(station_id)>1: #if its more than 1 then multiple stations
        print("**Multiple stations found...")
        return
    elif len(station_id) == 0: #else 0
        print("**No station found...")
        return

    # output the total ridership for each year for that station, in ascending order by year
    q="""select strftime('%Y', Ride_Date) as year, sum(Num_Riders) as total_riders
                      from Ridership
                      join Stations on Ridership.Station_ID = Stations.Station_ID
                      where Station_Name like ?
                      group by year
                      order by year;"""
    cursor.execute(q, (station_name,))
    rows = cursor.fetchall()

    if rows:
        print(f"Yearly Ridership at {station_id[0][0]}") #print yearly ridership
        years, rider = [], []
        for row in rows:
            year, total_riders = row
            print(f"{year} : {total_riders:,}")
            years.append(year)
            rider.append(total_riders)

        if input("\nPlot? (y/n) ").lower() == 'y':  #if user wants to see the plot
            plt.figure(figsize=(10, 6))
            plt.plot(years, rider, marker='o', linestyle='-', color='blue')
            plt.title(f"Annual Ridership for {station_id[0][0]}")
            plt.xlabel("Year")
            plt.ylabel("Total Ridership")
            plt.grid(True)
            plt.xticks(years, rotation=45)
            plt.tight_layout()
            plt.show()

    else: #if no then print no data
        print("No data found for the specified station and year range.")


def command_7(dbConn):
    #command 7

    cursor=dbConn.cursor()
    station_name = input("\nEnter a station name (wildcards _ and %): ")
    #year = input("Enter a year: ")

    # First, check if multiple stations match the wildcard name
    cursor.execute('select distinct Station_Name from Stations '
                   'where Station_Name like ?', (station_name,))
    stations = cursor.fetchall()

    if len(stations) == 0:
        print("**No station found...")
        return
    elif len(stations) > 1:
        print("**Multiple stations found...")
        return

    actual_station_name = stations[0][0]  # Get the station ID

    year=input("Enter a year: ")

    # query to get the ridership data by month for the specified year
    cursor.execute('''
            select strftime('%m', Ride_Date) as month, sum(Num_Riders) as total_riders
            from Ridership
            join Stations ON Ridership.Station_ID = Stations.Station_ID
            where Stations.Station_Name = ? and strftime('%Y', Ride_Date) = ?
            group by month
            order by month asc
        ''', (actual_station_name,year))

    rows = cursor.fetchall()

    print(f"Monthly Ridership at {actual_station_name} for {year}")

    if rows:
        for row in rows:
            month, total_riders = row
            print(f"{month}/{year} : {total_riders:,}")

    if input("\nPlot? (y/n) ").lower()=='y': #if user wants to see the plot
        month=[int(row_[0]) for row_ in rows]
        total_riders=[int(row_[1]) for row_ in rows]

        plt.figure(figsize=(10, 5))
        plt.plot(month, total_riders, marker='o', linestyle='-')
        plt.title(f"Monthly Ridership for {actual_station_name} Station ({year})")
        plt.xlabel("Month")
        plt.ylabel("Number of Riders")
        plt.xticks(range(1,13), [f"{m:02d}" for m in range(1,13)])
        plt.grid(True)
        plt.tight_layout()
        plt.show()


#command 8.1 for station name
def command_81(cursor, query):
    station_name = input(query)
    cursor.execute('select distinct Station_ID, Station_Name from Stations '
                   'where Station_Name like ?', (station_name,))
    stat_list = cursor.fetchall()

    if len(stat_list) > 1:
        print("**Multiple stations found...")
        return None
    elif len(stat_list) == 0:
        print("**No station found...")
        return None
    return stat_list[0]

#command 8.2 to get the data and print number, id, name and year
def command_82(cursor, station_number, station_id, station_name, year):

    q = """select strftime('%Y-%m-%d', Ride_Date) as day, sum(Num_Riders) as total_riders
               from Ridership
               where Station_ID = ? and strftime('%Y', Ride_Date) = ?
               group by day
               order by day;"""
    cursor.execute(q, (station_id, year))
    rows = cursor.fetchall()

    print(f"Station {station_number}: {station_id} {station_name}")

    # Print the first 5 and last 5 rows
    for row in rows[:5] + rows[-5:]:
        print(f"{row[0]} {row[1]}")

    return [datetime.strptime(row[0], "%Y-%m-%d") for row in rows], [day[1] for day in rows]
    #dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in rows]
    #rider = [row[1] for row in rows]

    #return dates, rider

#command 8.3 that compare ridership and find stations
def command_83(dates1, rider1, dates2, rider2, stat1_name, stat2_name, year):
    plt.figure(figsize=(12, 6))
    plt.plot(dates1, rider1, marker='o', linestyle='-', label=f'{stat1_name}')
    plt.plot(dates2, rider2, marker='o', linestyle='-', label=f'{stat2_name}')
    plt.title(f"Daily Ridership Comparison for {year}")
    plt.xlabel('Date')
    plt.ylabel('Total Ridership')
    plt.legend()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# command 8.4 compare stations
def command_84(dbConn):
    cursor = dbConn.cursor()

    year=input("\nYear to compare against? ")

    stat1 = command_81(cursor, "\nEnter station 1 (wildcards _ and %): ")
    if not stat1:
        return

    stat2 = command_81(cursor, "\nEnter station 2 (wildcards _ and %): ")
    if not stat2:
        return

    date1, rider1 = command_82(cursor, 1, stat1[0], stat1[1], year)
    date2, rider2 = command_82(cursor, 2, stat2[0], stat2[1], year)

    if input("\nPlot? (y/n) ").lower()=='y':
        command_83(date1, rider1, date2, rider2, stat1[1], stat2[1], year)

# command 8.5 to plot ridership comparison between two stations
def command_85(dbConn, latitude, longitude):
    if not (40 <= latitude <= 43):
        print("**Latitude entered is out of bounds...")
        return
    if not (-88 <= longitude <= -87):
        print("**Longitude entered is out of bounds...")
        return

    # Calculate the latitude and longitude boundaries for a one-mile range
    # lat_diff = 1 / 69  # 1 mile in latitude
    # long_diff = 1 / 51  # 1 mile in longitude
    #
    # lat_range = (round(latitude - lat_diff, 3), round(latitude + lat_diff, 3))
    # long_range = (round(longitude - long_diff, 3), round(longitude + long_diff, 3))

    latitude_range = (round(latitude - (1 / 69), 3), round(latitude + (1 / 69), 3))
    longitude_range = (round(longitude - (1 / 51), 3), round(longitude + (1 / 51), 3))

    # Query the database to find stations within these boundaries
    cursor = dbConn.cursor()

    cursor.execute("""
            select distinct Stations.Station_Name, Stops.Latitude, Stops.Longitude 
            from Stops 
            join Stations on Stops.Station_ID = Stations.Station_ID
            where Stops.Latitude between ? and ? and Stops.Longitude between ? and ?
            order by Stations.Station_Name
        """, (latitude_range[0], latitude_range[1], longitude_range[0], longitude_range[1]))

    stations_l = cursor.fetchall()

    if stations_l:
        print("\nList of Stations Within a Mile")
        for station in stations_l:
            print(f"{station[0]} : ({station[1]}, {station[2]})")
    else:
        print("**No stations found...")
        return


    response = input("\nPlot? (y/n) ") #input for yes or no
    if response.lower() == 'y':
        image = plt.imread("chicago.png")  # Load a map of Chicago and plot the stations on it
        plt.imshow(image, extent=[-87.9277, -87.5569, 41.7012, 42.0868])

    # Plot the stations
    for station in stations_l:
        plt.plot(station[2], station[1], 'o', color='blue')  # longitude, latitude
        plt.annotate(station[0], (station[2], station[1]), fontsize=8)

    plt.title("Stations Near You")
    plt.xlim([-87.9277, -87.5569])
    plt.ylim([41.7012, 42.0868])
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.tight_layout()
    plt.show()

def command_9():
    try:
        latitude = float(input("\nEnter a latitude: "))
        if not (40 <= latitude <= 43):  #checks the latitude between 40 and 43
            print("**Latitude entered is out of bounds...")
            return

        longitude = float(input("Enter a longitude: "))
        # Validate longitude
        if not (-88 <= longitude <= -87): #checks the latitude between -88 and -87
            print("**Longitude entered is out of bounds...")
            return

        command_85(dbConn, latitude, longitude)  #if condition passes then long and latitude goes to command_85
    except ValueError: #else invalid error
        print("**Error, invalid latitude or longitude...")


def handle_command_1():
    partial_name = input("\nEnter partial station name (wildcards _ and %): ")
    find_station_by_partial_name(partial_name) #connected to command-1

def handle_command_2():
    station_name = input("\nEnter the name of the station you would like to analyze: ")
    analyze_station_ridership(station_name)  #connected to command-2

def main():
    show_general_statistics() #menudriven program style

    while True:
        command = input("\nPlease enter a command (1-9, x to exit): ")

        if command == 'x':
            break
        elif command == '1':
            handle_command_1() #for command 1
        elif command == '2':
            handle_command_2() #for command 2
        elif command == '3':
            ridership_on_weekdays() #for command 3
        elif command == '4':
            stops_by_line_and_direction(dbConn) #for command 4
        elif command == '5':
            stops_by_line_and_direction_with_percentage() #for command 5
        elif command == '6':
            yearly_ridership_by_station(dbConn) #for command 6
        elif command == '7':
            command_7(dbConn) #for command 7
        elif command == '8':
            command_84(dbConn) #for command 8
        elif command == '9':
            command_9() #for command 9
        else:
            print("**Error, unknown command, try again...")

    dbConn.close() #close the connection

if __name__ == "__main__":
    main()
