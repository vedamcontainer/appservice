from flask import Blueprint, jsonify, request
from modules.security.permission_required import permission_required
from config import WRITE_ACCESS_TYPE
from modules.security.routines.get_user_and_db_details import get_user_and_db_details	
from modules.utilities.logger import logger
import traceback

create_default_tax_headers_api = Blueprint('create_default_tax_headers_api', __name__)

@create_default_tax_headers_api.route('/create_default_tax_headers', methods=['POST'])
@permission_required(WRITE_ACCESS_TYPE, __file__)
def create_default_tax_headers():

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
        
        mycursor = mydb.cursor()

        # Assuming the input data is in JSON format
        data = request.get_json()
        description = data.get('description', '').strip()  # Trim whitespace from the description

        # Validate the description field
        if not description:
            return jsonify({'error': 'Description is required and cannot be empty'}), 400

        created_by = appuserid  # Assuming created_by is the current user
        updated_by = appuserid  # Assuming updated_by is the current user

        # Insert query for default_tax_config table without header_id (AUTO_INCREMENT)
        insert_query = """
            INSERT INTO com.default_tax_config (description, created_at, updated_at)
            VALUES (%s, NOW(), NOW())
        """
        insert_values = (description,)  # Correctly formatted as a tuple

        logger.debug(f"{appuser} --> {__name__}: Executing query: {insert_query} with values: {insert_values}")
        mycursor.execute(insert_query, insert_values)
        mydb.commit()

        # Fetch the inserted header_id (auto-generated)
        header_id = mycursor.lastrowid

        mycursor.close()
        mydb.close()

        logger.info(f"{appuser} --> {__name__}: Default tax config created successfully with header_id {header_id}")

        return jsonify({'message': 'Default tax config created successfully', 'header_id': header_id}), 201

    except Exception as e:
        logger.error(f"{appuser} --> {__name__}: Error creating default tax config - {str(e)}")
        traceback.print_exc()  # Print the full stack trace for debugging
        return jsonify({'error': 'Internal Server Error'}), 500
