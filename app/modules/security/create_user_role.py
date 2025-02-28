from flask import Blueprint, jsonify, request
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from modules.security.permission_required import permission_required  # Import the decorator
from config import WRITE_ACCESS_TYPE    # Import WRITE_ACCESS_TYPE
from modules.utilities.logger import logger  # Import the logger module

create_user_role_data_api = Blueprint('create_user_role_data_api', __name__)

@create_user_role_data_api.route('/create_user_role', methods=['POST'])
@permission_required(WRITE_ACCESS_TYPE ,  __file__)  # Pass WRITE_ACCESS_TYPE as an argument
def create_user_role():
    authorization_header = request.headers.get('Authorization')
    try:
        company, instance, dbuser, mydb, appuser, appuserid, user_info, employee_info = get_user_and_db_details(authorization_header)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    
    if not appuser:
        return jsonify({"error": "Unauthorized. Application user " + {appuser} + "not found."}), 401
    
    logger.debug(f"{appuser} --> {__name__}: Entered in the create user role data function")

    # Retrieve user_role data from the request
    user_id = request.json.get('user_id', None)
    role_id = request.json.get('role_id', None)

    if user_id is None or role_id is None:
        return jsonify({'error': 'user_id and role_id must be provided'}), 400

    # Check if the provided user_id and role_id exist in the respective tables (users and roles)
    user_query = "SELECT id FROM adm.users WHERE id = %s"
    role_query = "SELECT id FROM adm.roles WHERE id = %s"
    mycursor = mydb.cursor()
    mycursor.execute(user_query, (user_id,))
    user_result = mycursor.fetchone()
    mycursor.execute(role_query, (role_id,))
    role_result = mycursor.fetchone()

    if user_result is None:
        logger.error(f"{appuser} --> {__name__}: The user id {user_id} is not found")
        return jsonify({'error': f'User with user_id {user_id} not found'}), 404

    if role_result is None:
        logger.error(f"{appuser} --> {__name__}: Role with role_id {role_id} not found")
        return jsonify({'error': f'Role with role_id {role_id} not found'}), 404


    # Create the user_role entry in the database
    query = "INSERT INTO adm.user_roles (user_id, role_id) VALUES (%s, %s)"
    values = (user_id, role_id)
    mycursor.execute(query, values)
    mydb.commit()

    # Close the cursor and connection
    mycursor.close()
    mydb.close()

    logger.debug(f"{appuser} --> {__name__}: User with user_id {user_id} and role_id {role_id} created successfully")

    # Return success message
    return jsonify({'message': f'User with user_id {user_id} and role_id {role_id} created successfully'})

