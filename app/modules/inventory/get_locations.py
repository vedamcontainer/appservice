# GET API for inv.locations
from flask import Blueprint, jsonify, request
from modules.security.permission_required import permission_required
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from config import READ_ACCESS_TYPE
from modules.utilities.logger import logger

locations_api = Blueprint('locations_api', __name__)

@locations_api.route('/get_locations', methods=['GET'])
@permission_required(READ_ACCESS_TYPE, __file__)
def get_locations():
    MODULE_NAME = __name__

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

        logger.debug(f"{appuser} --> {MODULE_NAME}: Entered the 'get locations' function")

        mycursor = mydb.cursor()

        location_id_param = request.args.get('location_id')
        location_name_param = request.args.get('location_name')
        warehouse_id_param = request.args.get('warehouse_id')
        warehouse_name_param = request.args.get('warehouse_name')

        query_params = {
            'location_id_param': location_id_param,
            'location_name_param': location_name_param,
            'warehouse_id_param': warehouse_id_param,
            'warehouse_name_param': warehouse_name_param
        }

        query = """
            SELECT l.location_id, l.location_name, l.location_type, l.description, l.capacity,
                   l.temperature_controlled, l.security_level, l.warehouse_id,
                   l.created_at, l.updated_at, l.created_by, l.updated_by,
                   w.warehouse_name AS warehouse_name
            FROM inv.locations l
            LEFT JOIN inv.warehouses w ON l.warehouse_id = w.warehouse_id
            WHERE (%(location_id_param)s IS NULL OR l.location_id = %(location_id_param)s)
              AND (%(location_name_param)s IS NULL OR l.location_name REGEXP %(location_name_param)s)
              AND (%(warehouse_id_param)s IS NULL OR l.warehouse_id = %(warehouse_id_param)s)
              AND (%(warehouse_name_param)s IS NULL OR w.warehouse_name REGEXP %(warehouse_name_param)s)
        """

        mycursor.execute(query, query_params)

        result = mycursor.fetchall()
        location_list = []

        columns = [desc[0] for desc in mycursor.description]
        column_indices = {column: index for index, column in enumerate(columns)}

        for row in result:
            location_dict = {}

            for column in columns:
                location_dict[column] = row[column_indices[column]]

            location_list.append(location_dict)

        mycursor.close()
        mydb.close()

        logger.debug(f"{appuser} --> {MODULE_NAME}: Successfully retrieved location data")

        return jsonify({'location_list': location_list})

    except Exception as e:
        logger.error(f"{appuser} --> {MODULE_NAME}: Error retrieving location data - {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500
