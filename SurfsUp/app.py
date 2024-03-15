# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# 1. Start at the homepage.
# List all the available routes.
@app.route("/")
def main():
    return(
        f'Welcome<br>'
        f'Available Routes:<br>'
        f'~~~~~~~~~~~~~~~~~~~~~~~~~<br>'
        f'1. Last 12 months of data<br>'
        f'/api/v1.0/precipitation <br>'
        f'............................<br>'
        f'2. List of stations<br>'
        f'/api/v1.0/stations <br>'
        f'............................<br>'
        f'3. Dates and temperature observations of the most-active station for the previous year of data<br>'
        f'/api/v1.0/tobs<br>'
        f'............................<br>'
        f'4. Minimum temperature, the average temperature, and the maximum temperature for date range 2017-04-21 to 2017-06-23 <br>'
        f'/api/v1.0/start-end <br>'
        f'~~~~~~~~~~~~~~~~~~~~~~~~~<br>'

    )

# 2.Convert the query results from your precipitation analysis 
# (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Retrieve last 12 months of data"""

    # query to get the most recent data
    latest_date = session.query(measurement.date).order_by(measurement.date.desc()).first().date

    # Calculate the date for the last year.
    last_year = dt.datetime.strptime(latest_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Perform a query to retrieve the date and precipitation scores
    prcp_scores = session.query(measurement.date, measurement.prcp).\
                    filter(measurement.date >= last_year).\
                    order_by(measurement.date).all()
    # Close the session
    session.close()
    # Create a dictionary using date as the key and prcp as the value
    prcp_dict = {}
    for date, prcp in prcp_scores:
        prcp_dict[date] = prcp

    return jsonify(prcp_dict)

# 3.Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    results = session.query(station.station).all()

    session.close()

    # Unravel results into a 1D array and convert to a list
    stations = list(np.ravel(results))
    return jsonify(stations=stations)


# 4.Query the dates and temperature observations of the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year
@app.route('/api/v1.0/tobs')
def temp():
    """Retrieve the temperature data for the most active station over the last year"""

    # query to get the most recent data
    latest_date = session.query(measurement.date).order_by(measurement.date.desc()).first().date
    # Calculate the date for the last year.
    last_year = dt.datetime.strptime(latest_date, '%Y-%m-%d') - dt.timedelta(days=365)
    # Query to retrieve the most active station id
    most_active = session.query(measurement.station, func.count(measurement.station)).\
                        group_by(measurement.station).\
                        order_by(func.count(measurement.station).desc()).first()
    most_active_id = most_active[0]
    # Query to get the dates and tempreture data for the  most active station
    temp_data = session.query(measurement.date, measurement.tobs).\
            filter(measurement.station == most_active_id).\
            filter(measurement.date >= last_year).all()
    # Close the session
    session.close()
    # create a dictionary inside a list that contains dates and temp for the most active station
    temp_list = []
    for date, temp in temp_data:
        temp_dict = {}
        temp_dict['date'] = date
        temp_dict['temp'] = temp
        temp_list.append(temp_dict)
        
    return jsonify(temp_list)

# # 5.Return a JSON list of the minimum temperature, the average temperature, 
# # and the maximum temperature for a specified start or start-end range.
# # For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
# # For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
@app.route('/api/v1.0/start-end')
def start_end(start=None, end=None):
    """Retieve the TMIN TAVG and TMAX"""

    start = input('Enter the start date ("YYYY-MM-DD")')
    end = input('Enter the end date ("YYYY-MM-DD")')
    if end and start:
        # If both start and end dates are provided
        temp_stats = session.query(func.min(measurement.tobs),
                                    func.avg(measurement.tobs),
                                    func.max(measurement.tobs)).\
                                    filter(measurement.date >= start,
                                        measurement.date <= end).all()
    elif start:
        # If only start date is provided
        temp_stats = session.query(func.min(measurement.tobs),
                                    func.avg(measurement.tobs),
                                    func.max(measurement.tobs)).\
                                    filter(measurement.date >= measurement).all()
    else:
        temp_stats = None

    # Close the session
    session.close()

    # Convert the result to JSON list
    results = [temp_stats[0][0], temp_stats[0][1], temp_stats[0][2]]
    result = {
            "start_date": start,
            "end_date": end,
            "TMIN": temp_stats[0][0],
            "TAVG": temp_stats[0][1],
            "TMAX": temp_stats[0][2]
        }

    return jsonify(result)



if __name__ == '__main__':
    app.run(debug=True)