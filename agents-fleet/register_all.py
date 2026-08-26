import sys
from refund_agent import register_on_startup as reg_refund
from settlement_agent import register_on_startup as reg_settlement
from fraud_analysis_agent import register_on_startup as reg_fraud
from support_agent import register_on_startup as reg_support
from customer_service_agent import register_on_startup as reg_cust_srv

def main():
    print("Registering Agent Fleet with Sentinel Safety Service...")
    reg_refund()
    reg_settlement()
    reg_fraud()
    reg_support()
    reg_cust_srv()
    print("All agents registered successfully.")

if __name__ == "__main__":
    main()
