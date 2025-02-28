from flask import Blueprint, jsonify, request
from modules.admin.databases.mydb import get_database_connection
from modules.security.permission_required import permission_required  # Import the decorator
from config import DELETE_ACCESS_TYPE    # Import WRITE_ACCESS_TYPE
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from modules.utilities.logger import logger  # Import the logger module

delete_user_modules_api = Blueprint('delete_user_modules_api', __name__)

@delete_user_modules_api.route('/delete_user_modules', methods=['DELETE'])
@permission_required(DELETE_ACCESS_TYPE ,  __file__)  # Pass WRITE_ACCESS_TYPE as an argument
def delete_user_modules():

    authorization_header = request.headers.get('Authorization')
    try:
        company, instance, dbuser, mydb, appuser, appuserid, user_info, employee_info = get_user_and_db_details(authorization_header)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    
    if not appuser:
        return jsonify({"error": "Unauthorized. Application user " + {appuser} + "not found."}), 401
    
    
    logger.debug(f"{appuser} --> {__name__}: Entered in the delete user modules data function")    
    mydb = get_database_connection(appuser, __name__)

    # Retrieve user_id and modules from the request
    user_id = request.json.get('user_id', None)
    modules = request.json.get('modules', [])
    logger.debug(f"{appuser} --> {__name__}: Deleting modules for user_id {user_id}")

    if user_id is None:
        logger.error(f"{appuser} --> {__name__}: Missing user_id in the request payload")
        return jsonify({'error': 'The user_id field is required to identify the user'}), 400

    if not modules:
        logger.error(f"{appuser} --> {__name__}: Missing or empty modules list in the request")
        return jsonify({'error': 'The modules field must be provided as a non-empty list of module names'}), 400

    # Check if the provided user_id exists in the database
    query = "SELECT * FROM adm.users WHERE id = %s"
    mycursor = mydb.cursor()
    mycursor.execute(query, (user_id,))
    existing_user = mycursor.fetchone()

    if not existing_user:
        logger.error(f"{appuser} --> {__name__}: User with user_id {user_id} does not exist")
        return jsonify({'error': f'User with user_id {user_id} does not exist'}), 404


    # Loop through the list of modules and delete the corresponding rows
    for module in modules:
        # Check if the provided module exists in the database
        query = "SELECT * FROM adm.user_module_permissions WHERE user_id = %s AND module = %s"
        mycursor.execute(query, (user_id, module))
        existing_permission = mycursor.fetchone()

        if not existing_permission:
            # If the combination does not exist, skip this module and proceed with the next one
            continue

        # If the combination exists, delete the row
        delete_query = "DELETE FROM adm.user_module_permissions WHERE user_id = %s AND module = %s"
        mycursor.execute(delete_query, (user_id, module))
        mydb.commit()

    # Close the cursor
    mycursor.close()

    # Close the connection
    mydb.close()

    logger.debug(f"{appuser} --> {__name__}: User with user_id {user_id} module permissions deleted successfully")

    # Return success message
    return jsonify({'message': f'User with user_id {user_id} module permissions deleted successfully'})

