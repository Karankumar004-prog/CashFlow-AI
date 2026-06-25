import sys

# Add skills directory to path just in case
sys.path.insert(0, ".")

from tests.test_cleaner import (
    test_clean_prefixes,
    test_clean_numbers_and_hashes,
    test_clean_states_and_utilities,
    test_clean_empty
)
from tests.test_rules import (
    test_match_netflix,
    test_match_landlord_rent,
    test_no_match
)
from tests.test_regex import (
    test_match_regex_payroll,
    test_match_regex_amazon_refund,
    test_match_regex_amazon_expense,
    test_match_regex_vanguard,
    test_match_regex_student_loan,
    test_match_regex_savings_transfer,
    test_match_regex_coned,
    test_no_regex_match
)
from tests.test_memory import (
    test_match_user_memory_success,
    test_match_user_memory_fail
)
from tests.test_pipeline import (
    test_pipeline_rules,
    test_pipeline_regex,
    test_pipeline_memory,
    test_pipeline_fallback_expense,
    test_pipeline_fallback_income,
    test_pipeline_ai_fallback,
    test_pipeline_telemetry,
    test_pipeline_csv_metadata_classification,
    test_pipeline_new_stage0_mappings
)
from tests.test_dataset_integration import test_dataset_integration_run
from tests.test_financial_analysis import (
    test_calculator_savings_rate,
    test_scorecard_points,
    test_pipeline_integration
)
from tests.test_behavior_analysis import (
    test_category_concentration_math,
    test_risk_deficit_and_liquidity,
    test_risk_subscription_sprawl,
    test_pipeline_behavior_integration,
    test_calculate_income_concentration,
    test_weekly_spending_and_transparency
)
from tests.test_financial_coach import test_financial_coach_mock_run
from tests.test_report_generation import test_report_generation_output
from tests.test_schema_detection import (
    test_schema_detection_real_headers,
    test_schema_detection_standard_headers
)

def run_all_tests():
    tests = [
        # Cleaner tests
        test_clean_prefixes,
        test_clean_numbers_and_hashes,
        test_clean_states_and_utilities,
        test_clean_empty,
        
        # Rules matcher tests
        test_match_netflix,
        test_match_landlord_rent,
        test_no_match,
        
        # Regex matcher tests
        test_match_regex_payroll,
        test_match_regex_amazon_refund,
        test_match_regex_amazon_expense,
        test_match_regex_vanguard,
        test_match_regex_student_loan,
        test_match_regex_savings_transfer,
        test_match_regex_coned,
        test_no_regex_match,
        
        # Memory matcher tests
        test_match_user_memory_success,
        test_match_user_memory_fail,
        
        # Pipeline orchestrator tests
        test_pipeline_rules,
        test_pipeline_regex,
        test_pipeline_memory,
        test_pipeline_fallback_expense,
        test_pipeline_fallback_income,
        test_pipeline_ai_fallback,
        test_pipeline_telemetry,
        test_pipeline_csv_metadata_classification,
        test_pipeline_new_stage0_mappings,
        
        # Dataset integration test
        test_dataset_integration_run,
        
        # Financial Analysis tests
        test_calculator_savings_rate,
        test_scorecard_points,
        test_pipeline_integration,
        
        # Behavior Analysis tests
        test_category_concentration_math,
        test_risk_deficit_and_liquidity,
        test_risk_subscription_sprawl,
        test_pipeline_behavior_integration,
        test_calculate_income_concentration,
        test_weekly_spending_and_transparency,
        
        # Financial Coach tests
        test_financial_coach_mock_run,
        
        # Report Generation tests
        test_report_generation_output,
        
        # Schema Detection tests
        test_schema_detection_real_headers,
        test_schema_detection_standard_headers
    ]
    
    passed = 0
    failed = 0
    
    print("Running CashFlow AI End-to-End Unit & Integration Tests...\n" + "="*65)
    for t in tests:
        try:
            t()
            print(f"✓ PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAIL: {t.__name__} - Assertion failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ FAIL: {t.__name__} - Exception encountered: {e}")
            failed += 1
            
    print("="*65 + f"\nSummary: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
