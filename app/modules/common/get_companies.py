from flask import Blueprint, jsonify, request
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from modules.security.permission_required import permission_required
from config import READ_ACCESS_TYPE
from modules.utilities.logger import logger

company_api = Blueprint('company_api', __name__)

@company_api.route('/get_companies', methods=['GET'])
@permission_required(READ_ACCESS_TYPE, __file__)
def get_companies():
    try:
		
        authorization_header = request.headers.get('Authorization')

        try:
            company, instance, dbuser, mydb, appuser, appuserid, user_info, employee_info = get_user_and_db_details(authorization_header)
            logger.debug(f"{appuser} --> {__name__}: Successfully retrieved user details from the token.")
        except ValueError as e:
            logger.error(f"Failed to retrieve user details from token. Error: {str(e)}")
            return jsonify({"error": str(e)}), 401
        
        if not appuser:
            logger.error(f"Unauthorized access attempt: {appuser} --> {__name__}: Application user not found.")
            return jsonify({"error": "Unauthorized. Username not found."}), 401
  
        logger.debug(f"{appuser} --> {__name__}: Entered the 'get companies' function")

        mycursor = mydb.cursor()

        company_id = request.args.get('company_id')
        company_name = request.args.get('company_name')

        query = """
            SELECT
                c.id AS company_id,
                c.group_company_id,
                c.name AS company_name,
                c.description AS company_description,
                c.local_cur_id,
                c.home_cur_id,
                c.reporting_cur_id,
                g.name AS group_company_name,
                g.description AS group_company_description,
                cu_local.currencycode AS local_currency_code,
                cu_local.currencyname AS local_currency_name,
                cu_local.currencysymbol AS local_currency_symbol,
                cu_home.currencycode AS home_currency_code,
                cu_home.currencyname AS home_currency_name,
                cu_home.currencysymbol AS home_currency_symbol,
                cu_reporting.currencycode AS reporting_currency_code,
                cu_reporting.currencyname AS reporting_currency_name,
                cu_reporting.currencysymbol AS reporting_currency_symbol,
                ctc.description AS company_tax_codes_description,
                dah.header_name AS default_account_header_name,
                c.created_at,
                c.updated_at,
                c.created_by,
                c.updated_by,
                c.default_tax_code_id,
                c.default_account_header_id
            FROM com.company c
            JOIN com.group_company g ON c.group_company_id = g.id
            LEFT JOIN com.currency cu_local ON c.local_cur_id = cu_local.currency_id
            LEFT JOIN com.currency cu_home ON c.home_cur_id = cu_home.currency_id
            LEFT JOIN com.currency cu_reporting ON c.reporting_cur_id = cu_reporting.currency_id
            LEFT JOIN com.default_tax_config ctc ON c.default_tax_code_id = ctc.header_id
            LEFT JOIN fin.default_account_headers dah ON c.default_account_header_id = dah.header_id
        """

        params = {}

        if company_id:
            query += " WHERE c.id = %(company_id)s"
            params['company_id'] = company_id
        elif company_name:
            query += " WHERE c.name REGEXP %(company_name)s"
            params['company_name'] = company_name

        mycursor.execute(query, params)

        result = mycursor.fetchall()
        company_list = []

        columns = [desc[0] for desc in mycursor.description]
        column_indices = {column: index for index, column in enumerate(columns)}

        for row in result:
            company_dict = {}

            for column in columns:
                company_dict[column] = row[column_indices[column]]

            company_list.append(company_dict)

        mycursor.close()
        mydb.close()

        logger.debug(f"{appuser} --> {__name__}: Successfully retrieved company data")

        return jsonify({'company_list': company_list})

    except Exception as e:
        logger.error(f"{appuser} --> {__name__}: Error retrieving company data - {str(e)}")
        import traceback
        traceback.print_exc()  # Add this line to print the full stack trace
        return jsonify({'error': 'Internal Server Error'}), 500
