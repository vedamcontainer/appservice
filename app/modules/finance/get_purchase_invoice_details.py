from flask import Blueprint, jsonify, request
from modules.security.permission_required import permission_required
from modules.security.routines.get_user_and_db_details import get_user_and_db_details
from config import READ_ACCESS_TYPE
from modules.utilities.logger import logger

purchase_invoice_details_api = Blueprint('purchase_invoice_details_api', __name__)

@purchase_invoice_details_api.route('/get_purchase_invoice_details', methods=['GET'])
@permission_required(READ_ACCESS_TYPE, __file__)
def get_purchase_invoice_details():
    

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

        logger.debug(f"{appuser} --> {__name__}: Entered the 'get_purchase_invoice_details' function")

        invalid_params_present = any(param for param in request.args.keys() if param not in ['header_id', 'invoice_number', 'partnerid', 'invoicedate', 'status', 'tax_id', 'company_id', 'currency_id', 'department_id', 'transaction_source'])
        if invalid_params_present:
            return jsonify({'error': 'Invalid query parameter(s) detected'}), 400

        header_id_str = request.args.get('header_id')
        header_id = int(header_id_str.strip('"')) if header_id_str is not None else None
        invoice_number_str = request.args.get('invoice_number')
        invoice_number = int(invoice_number_str.strip('"')) if invoice_number_str is not None else None
        partnerid_str = request.args.get('partnerid')
        partnerid = int(partnerid_str.strip('"')) if partnerid_str is not None else None
        invoicedate = request.args.get('invoicedate')
        status_list = request.args.getlist('status')
        tax_id_str = request.args.get('tax_id')
        tax_id = int(tax_id_str.strip('"')) if tax_id_str is not None else None
        company_id_str = request.args.get('company_id')
        company_id = int(company_id_str.strip('"')) if company_id_str is not None else None
        currency_id_str = request.args.get('currency_id')
        currency_id = int(currency_id_str.strip('"')) if currency_id_str is not None else None
        department_id_str = request.args.get('department_id')
        department_id = int(department_id_str.strip('"')) if department_id_str is not None else None
        transaction_source_str = request.args.get('transaction_source')
        
        mycursor = mydb.cursor()

        query = """
            SELECT 
                p.header_id, p.invoice_number, p.partnerid, p.invoicedate, p.totalamount, p.status, 
                p.payment_terms, p.payment_duedate, p.tax_id, p.currency_id, p.department_id, p.company_id, 
                p.transaction_source, -- Added transaction_source field
                p.created_at, p.updated_at, p.created_by, p.updated_by,
                b.partnername, b.email, b.phone, b.address, b.city, b.state, b.postalcode, b.country,
                d.department_name, d.manager_id,
                c.name AS company_name, c.id AS company_id,
                cur.currencycode, cur.currencyname, cur.currencysymbol
            FROM fin.purchaseinvoice p
            LEFT JOIN com.businesspartner b ON p.partnerid = b.partnerid
            LEFT JOIN com.department d ON p.department_id = d.id
            LEFT JOIN com.company c ON p.company_id = c.id
            LEFT JOIN com.currency cur ON p.currency_id = cur.currency_id
            WHERE 1=1
        """

        if header_id:
            query += f" AND p.header_id = {header_id}"
        if invoice_number:
            query += f" AND p.invoice_number = {invoice_number}"
        if partnerid:
            query += f" AND p.partnerid = {partnerid}"
        if invoicedate:
            query += f" AND p.invoicedate = '{invoicedate}'"
        if status_list:
            status_conditions = " OR ".join([f"p.status = '{status}'" for status in status_list])
            query += f" AND ({status_conditions})"
        if tax_id:
            query += f" AND p.tax_id = {tax_id}"
        if company_id:
            query += f" AND p.company_id = {company_id}"
        if currency_id:
            query += f" AND p.currency_id = {currency_id}"
        if department_id:
            query += f" AND p.department_id = {department_id}"
        if transaction_source_str:
            query += f" AND p.transaction_source = '{transaction_source_str}'" 

        mycursor.execute(query)

        result = mycursor.fetchall()
        purchase_invoice_headers= []

        columns = [desc[0] for desc in mycursor.description]
        column_indices = {column: index for index, column in enumerate(columns)}

        for row in result:
            purchase_invoice_details_dict = {}

            for column in columns:
                purchase_invoice_details_dict[column] = row[column_indices[column]]

            purchase_invoice_headers.append(purchase_invoice_details_dict)

        mycursor.close()
        mydb.close()

        logger.debug(f"{appuser} --> {__name__}: Successfully retrieved purchase invoice details data")

        return jsonify({'purchase_invoice_headers': purchase_invoice_headers})

    except Exception as e:
        logger.error(f"{appuser} --> {__name__}: Error retrieving purchase invoice details data - {str(e)}")
        import traceback
        traceback.print_exc()  # Add this line to print the full stack trace
        return jsonify({'error': 'Internal Server Error'}), 500
