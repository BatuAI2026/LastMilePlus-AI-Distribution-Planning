import pandas as pd
import numpy as np

# Constants
SEASONALITY_INDEX = 1.09
MONTHS_STOCK = 3

# Function to calculate rolling average monthly consumption

def calculate_rolling_amc(data):
    data['RollingAMC'] = data.groupby(['FacilityID', 'ProductID'])['MonthlyConsumption'].transform(lambda x: x.rolling(window=3).mean())
    return data

# Function to adjust AMC with seasonality index

def adjust_amc_with_seasonality(data):
    data['AdjustedAMC'] = data['RollingAMC'] * SEASONALITY_INDEX
    return data

# Function to calculate target stock

def calculate_target_stock(data):
    data['TargetStock'] = data['AdjustedAMC'] * MONTHS_STOCK
    return data

# Function to calculate net need

def calculate_net_need(data, march_closing_balance):
    data['NetNeed'] = data['TargetStock'] - march_closing_balance
    return data

# Function to determine carrier assignment

def assign_carriers(data):
    conditions = [
        (data['FacilityType'] == 'Government'),
        (data['FacilityType'].isin(['CHAM', 'Private']))
    ]
    choices = ['3PL-Alpha', 'Partner-HealthPlus']
    data['Carrier'] = np.select(conditions, choices, default='Unknown')
    return data

# Function to identify overstocking and understocking

def identify_stock_scenarios(data):
    data['StockScenario'] = np.where(data['NetNeed'] > 0, 'Understocking', 'Overstocking')
    return data

# Function to generate reports

def generate_reports(data):
    facility_summary = data.groupby(['FacilityID']).agg({'NetNeed': 'sum', 'StockScenario': 'first'}).reset_index()
    district_summary = data.groupby(['District']).agg({'NetNeed': 'sum'}).reset_index()
    
    # Export to Excel
    with pd.ExcelWriter('distribution_plans.xlsx') as writer:
        data.to_excel(writer, sheet_name='DetailedPlan', index=False)
        facility_summary.to_excel(writer, sheet_name='FacilitySummary', index=False)
        district_summary.to_excel(writer, sheet_name='DistrictSummary', index=False)

# Main execution function

def main():
    # Load data
    lmis_data = pd.read_csv('lmis_data.csv')  # Sample LMIS data must be available

    # Processing
    lmis_data = calculate_rolling_amc(lmis_data)
    lmis_data = adjust_amc_with_seasonality(lmis_data)
    lmis_data['MarchClosingBalance'] = lmis_data.groupby(['FacilityID'])['ClosingBalance'].shift(1)  # Assuming ClosingBalance is the previous month's data
    lmis_data = calculate_target_stock(lmis_data)
    lmis_data = calculate_net_need(lmis_data, lmis_data['MarchClosingBalance'])
    lmis_data = assign_carriers(lmis_data)
    lmis_data = identify_stock_scenarios(lmis_data)

    # Generate output
    generate_reports(lmis_data)

if __name__ == '__main__':
    main()