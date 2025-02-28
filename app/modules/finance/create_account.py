from flask import Blueprint, jsonify, request
from modules.admin.databases.mydb import get_database_connection
from modules.security.permission_required import permission_required
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from config import WRITE_ACCESS_TYPE
from flask_jwt_extended import decode_token
from modules.security.get_user_from_token import get_user_from_token
from modules.utilities.logger import logger

accounts_api = Blueprint('accounts_api', __name__)

@accounts_api.route('/create_account', methods=['POST'])
@permission_required(WRITE_ACCESS_TYPE, __file__)
def create_account():
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
        # Log entry point
        logger.debug(f"{appuser} --> {__name__}: Entered the 'create_account' function")


        if request.content_type == 'application/json':
            data = request.get_json()
            print(data)
        else:
            data = request.form


        department_id = data.get('department_id')
        if department_id == '':
            department_id = None

        # Log the received data
        logger.debug(f"{appuser} --> {__name__}: Received data: {data}")

        # Assuming your accounts table has columns like account_number, account_name, etc.
        insert_query = """
            INSERT INTO fin.accounts (account_number, account_name, account_category, account_type, opening_balance, currency_id, bank_name, branch_name, account_holder_name, contact_number, email, address, is_active, department_id, company_id, created_by, updated_by,default_account)
            VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """

        # Assuming the account_data dictionary contains the necessary keys
        insert_values = (
            data.get('account_number'),
            data.get('account_name'),
            data.get('account_category'),
            data.get('account_type'),
            data.get('opening_balance'),
            int(data.get('currency_id')),
            data.get('bank_name'),
            data.get('branch_name'),
            data.get('account_holder_name'),
            data.get('contact_number'),
            data.get('email'),
            data.get('address'),
            data.get('is_active'),
            department_id,
            data.get('company_id'),
            appuserid,  # created_by
            appuserid,   # updated_by
            data.get('default_account')
        )

        mycursor = mydb.cursor()

        try:
            mycursor.execute(insert_query, insert_values)
            mydb.commit()

            # Log success and close the cursor and connection
            logger.info(f"{appuser} --> {__name__}: Account data created successfully")
            mycursor.close()
            mydb.close()
            return jsonify({'message': 'Account created successfully'}), 200

        except Exception as e:
            # Log the error and close the cursor and connection
            logger.error(f"{appuser} --> {__name__}: Unable to create account data: {str(e)}")
            mycursor.close()
            mydb.close()
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        # Log any exceptions
        logger.error(f"{appuser} --> {__name__}: An error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500
