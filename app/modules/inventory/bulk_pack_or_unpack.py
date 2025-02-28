from flask import jsonify, request, Blueprint
from modules.security.permission_required import permission_required
from config import WRITE_ACCESS_TYPE
from modules.products.routines.uom_conversion import uom_conversion
from modules.inventory.routines.bulk_packing_or_unpacking import bulk_packing_or_unpacking
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from modules.utilities.logger import logger

bulk_pack_or_unpack_api = Blueprint('bulk_pack_or_unpack_api', __name__)

@bulk_pack_or_unpack_api.route('/bulk_pack_or_unpack_api', methods=['POST'])
@permission_required(WRITE_ACCESS_TYPE, __file__)
def bulk_pack_or_unpack():
    MODULE_NAME = __name__
    mydb1 = None
    mycursor = None

    try:
        # Log request details
        logger.info(f"Received request: {request.method} {request.url}")

        # Extract input data from the request body
        data = request.get_json(silent=True)            

        authorization_header = request.headers.get('Authorization')

        try:
            company, instance, dbuser, mydb1, appuser, appuserid, user_info, employee_info = get_user_and_db_details(authorization_header)
            logger.debug(f"{appuser} --> {__name__}: Successfully retrieved user details from the token.")
        except ValueError as e:
            logger.error(f"Failed to retrieve user details from token. Error: {str(e)}")
            return jsonify({"error": str(e)}), 401
        
        if not appuser:
            logger.error(f"Unauthorized access attempt: {appuser} --> {__name__}: Application user not found.")
            return jsonify({"error": "Unauthorized. Username not found."}), 401

        # Extract individual input parameters
        input_item_id = data.get('input_item_id')
        input_source_uom_id = data.get('input_source_uom_id')
        input_target_uom_id = data.get('input_target_uom_id')
        input_warehouse_id = data.get('input_warehouse_id')
        input_location_id = data.get('input_location_id')
        input_zone_id = data.get('input_zone_id')
        input_aisle_id = data.get('input_aisle_id')
        input_row_id = data.get('input_row_id')
        input_rack_id = data.get('input_rack_id')
        input_bin_id = data.get('input_bin_id')
        input_transaction_id = data.get('input_transaction_id')
        input_transaction_type = data.get('input_transaction_type')

        if input_source_uom_id == input_target_uom_id:
            error_message = "Fail : Source UOM and Target UOM cannot be the same."
            logger.error(error_message)
            return error_message, 400

        if all(data.get(field) is not None for field in ['input_item_id', 'input_source_uom_id', 'input_target_uom_id']):
            # Check if at least one optional field is present
            optional_fields = ['input_warehouse_id', 'input_location_id', 'input_zone_id', 'input_aisle_id', 'input_row_id', 'input_rack_id', 'input_bin_id']
            if any(data.get(field) is not None for field in optional_fields):
                logger.error(f"All mandatory fields are present and at least one optional field is present.")
            else:
                logger.error(f"At least one warehouse location field is required")
                return 'Fail :At least one warehouse location field is required', 400
        else:
            logger.error(f"Missing mandatory parameters in the request")
            return 'Fail : Missing mandatory parameters in the request', 400

        # Log individual input parameters
        logger.debug(f"Input Item ID: {input_item_id}")
        logger.debug(f"Input Source UOM ID: {input_source_uom_id}")
        logger.debug(f"Input Target UOM ID: {input_target_uom_id}")
        logger.debug(f"Input input_warehouse_id: {input_warehouse_id}")
        logger.debug(f"Input input_location_id: {input_location_id}")
        logger.debug(f"Input input_zone_id: {input_zone_id}")
        logger.debug(f"Input input_aisle_id: {input_aisle_id}")
        logger.debug(f"Input input_row_id: {input_row_id}")
        logger.debug(f"Input input_rack_id: {input_rack_id}")
        logger.debug(f"Input input_bin_id: {input_bin_id}")

        # Log database connection
        with mydb1 as mydb:
            logger.debug(f"Database Connection established for User ID: {appuser}")
            print("Reached Bulkpack function")
            with mydb.cursor() as mycursor:
                inventory_query = "SELECT * FROM inv.item_inventory WHERE item_id = %s AND uom_id = %s AND (status != 'Yes' OR status IS NULL)"

                mycursor.execute(inventory_query, (input_item_id, input_source_uom_id))

                fetched_row = mycursor.fetchall()

                if not fetched_row:
                    logger.info("No row found for the specified parameters or the selected inventory is reserved")
                    return 'Fail: No row found for the specified parameters or the selected inventory is reserved', 400

                total_quantity = sum(row[5] for row in fetched_row)
                concatenated_rows = []
                for row in fetched_row:
                    concatenated_values = '|'.join(map(str, row))
                    concatenated_rows.append(concatenated_values)

                # Join the concatenated rows using a semicolon as a delimiter
                target_additional_info = ';'.join(concatenated_rows)
                logger.debug(f"Fetched Rows total quantity from Inventory table: {total_quantity}")
                conversion_results, status_code = uom_conversion(input_source_uom_id, total_quantity, input_target_uom_id, mydb, appuser, MODULE_NAME)
                if status_code == 400:
                    logger.info("Not processed successfully")
                    return "Fail : UOM conversion is not possible", 422
                input_params = {
                    'input_item_id': input_item_id,
                    'input_source_uom_id': input_source_uom_id,
                    'input_target_uom_id': input_target_uom_id,
                    'input_warehouse_id': input_warehouse_id,
                    'input_location_id': input_location_id,
                    'input_zone_id': input_zone_id,
                    'input_aisle_id': input_aisle_id,
                    'input_row_id': input_row_id,
                    'input_rack_id': input_rack_id,
                    'input_bin_id': input_bin_id,
                    'input_transaction_id' : input_transaction_id,
                    'input_transaction_type': input_transaction_type,
                    'target_additional_info': target_additional_info,
                    'mydb': mydb,
                    'appuser': appuser,
                    'MODULE_NAME': MODULE_NAME,
                    'created_by': appuserid,
                    'updated_by': appuserid
                }

                result, status_code = bulk_packing_or_unpacking(input_params, conversion_results)
                logger.info("Bulk_packing_or_unpacking call results and status code ",result,status_code)
                if status_code == 200:
                    inventory_id_values = [row[0] for row in fetched_row]
                    logger.debug(f"Now the data will be deleted for the inventory ids",inventory_id_values)
                    delete_query = "DELETE FROM inv.item_inventory WHERE inventory_id IN (%s)" % ','.join(map(str, inventory_id_values))
                    mycursor.execute(delete_query)
                else:
                    logger.info("Item Inventory consolidation or UOM conversion is not done")
                    return "Fail : Item Inventory consolidation or UOM conversion is not done", status_code
            mydb.commit()
            if mydb:
                mydb.close()

        if mydb1:
            mydb1.close()            

        # Log response
        logger.info("Request processed successfully")
        return f"Success: Item Inventory {input_transaction_type} or UOM conversion transaction No is {input_transaction_id}", 200


    except Exception as e:
        if mydb1:
            mydb1.close() 
        logger.error(f"Error occurred: {str(e)}")
        return "Exception Error Item Inventory consolidation or UOM conversion is not done", 500

