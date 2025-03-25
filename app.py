from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
from textwrap import dedent

app = Flask(__name__)
CORS(app)

@app.route('/process', methods=['POST'])
def process_data():
    try:
        # Get the multiline string from the request
        data_string = request.json.get('data')
        spark_flag = request.json.get('pysparkFlag')
        pandas_flag = request.json.get('pandasFlag')

        if not data_string:
            return jsonify({"error": "No data provided"}), 400

        # Step 1: Split the string into individual lines
        lines = data_string.strip().split('\n')

        # Step 2: Initialize lists to hold the header and data
        header = []
        data = []

        # Step 3: Parse the lines
        for line in lines:
            line = line.strip()

            # Check for header line (contains '|' but not '+')
            if line.startswith('|') and '+' not in line:
                if not header:  # If header is not set yet, this is the header row
                    header = [col.strip() for col in line.strip('|').split('|')]

            # Check for data lines (contains '|' and not just a border)
            if line.startswith('|') and '+' not in line and header:
                print("yess..i checked here")
                data_row = [col.strip() for col in line.strip('|').split('|')]
                print(data_row)  
                data.append(data_row)

        # Step 4: Create code snippet for DataFrame
        # Assuming 'data' and 'header' are defined earlier in your code
        data_code = ',\n    '.join([repr(row) for row in data[1:]])  # Use repr for proper string representation
        spark_snippet = dedent(f"""
        \n# Create PySpark SparkSession
        \nfrom pyspark.sql import SparkSession
        \nspark = SparkSession.builder \\
            .master("local[1]") \\
            .appName("Spark") \\
            .getOrCreate()
        """)

        spark_snippet_end = dedent(f"""
        sparkDF = spark.createDataFrame(df)
        """)

        code_snippet = dedent(f"""\
        \nimport pandas as pd
        \n#Create Pandas DataFrame
        \ndata = [
            {data_code}
        ]
        \ndf = pd.DataFrame(data, columns={header})
        \nprint(df)
        """)

        if spark_flag or (spark_flag and pandas_flag):
            return jsonify({"dataframe": (spark_snippet + code_snippet + spark_snippet_end).strip()}), 200
        elif pandas_flag:
            return jsonify({"dataframe": code_snippet.strip()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the app in production mode
    app.run(host='0.0.0.0', port=5000)
    #app.run(host='127.0.0.1', port=5000)
