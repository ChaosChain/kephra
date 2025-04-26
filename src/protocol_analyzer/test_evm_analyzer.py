"""
Test cases for the EVMAnalyzer class.
"""

import pytest
from .evm_analyzer import EVMAnalyzer, EVMMetrics, OptimizationRecommendation

# Sample contract code for testing
SAMPLE_CONTRACT = """
pragma solidity ^0.8.0;

contract TestContract {
    uint256 public value;
    mapping(address => uint256) public balances;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
"""

@pytest.fixture
def analyzer():
    return EVMAnalyzer(SAMPLE_CONTRACT)

def test_basic_metrics(analyzer):
    """Test basic EVM metrics calculation."""
    metrics = analyzer.analyze()
    
    assert isinstance(metrics, EVMMetrics)
    assert metrics.total_cost > 0
    assert metrics.storage_cost > 0
    assert metrics.memory_cost > 0
    assert metrics.computation_cost > 0
    assert metrics.bytecode_size > 0
    assert 0 <= metrics.storage_efficiency <= 100
    assert metrics.stack_depth >= 0

def test_feature_compatibility(analyzer):
    """Test feature compatibility detection."""
    metrics = analyzer.analyze()
    
    # Check that feature compatibility is a dictionary
    assert isinstance(metrics.feature_compatibility, dict)
    
    # Check for common EVM features
    expected_features = ["staticcall", "create2", "chainid"]
    for feature in expected_features:
        assert feature in metrics.feature_compatibility
        assert isinstance(metrics.feature_compatibility[feature], bool)

def test_optimization_recommendations(analyzer):
    """Test generation of optimization recommendations."""
    recommendations = analyzer.generate_recommendations()
    
    assert isinstance(recommendations, list)
    for rec in recommendations:
        assert isinstance(rec, OptimizationRecommendation)
        assert rec.category in ["storage", "memory_ops", "computation"]
        assert rec.severity in ["low", "medium", "high"]
        assert isinstance(rec.description, str)
        assert isinstance(rec.potential_savings, int)
        assert isinstance(rec.code_changes, list)

def test_summary_generation(analyzer):
    """Test summary generation."""
    summary = analyzer.get_summary()
    
    assert isinstance(summary, dict)
    assert "metrics" in summary
    assert "total_gas_cost" in summary["metrics"]
    assert "storage_efficiency" in summary["metrics"]
    assert "stack_depth" in summary["metrics"]
    assert "bytecode_size" in summary["metrics"]
    
    if "recommendations" in summary:
        assert isinstance(summary["recommendations"], list)
        for rec in summary["recommendations"]:
            assert "category" in rec
            assert "severity" in rec
            assert "potential_savings" in rec

def test_storage_layout_analysis(analyzer):
    """Test storage layout analysis."""
    metrics = analyzer.analyze()
    
    # Check storage efficiency
    assert 0 <= metrics.storage_efficiency <= 100
    
    # Generate recommendations
    recommendations = analyzer.generate_recommendations()
    storage_recs = [r for r in recommendations if r.category == "storage"]
    
    # Verify storage recommendations
    for rec in storage_recs:
        assert rec.severity in ["low", "medium", "high"]
        assert rec.potential_savings >= 0
        assert len(rec.code_changes) > 0

def test_computation_pattern_analysis(analyzer):
    """Test computation pattern analysis."""
    recommendations = analyzer.generate_recommendations()
    compute_recs = [r for r in recommendations if r.category == "computation"]
    
    # Verify computation recommendations
    for rec in compute_recs:
        assert rec.severity in ["low", "medium", "high"]
        assert rec.potential_savings >= 0
        assert len(rec.code_changes) > 0
        
    # Test with a computation-heavy contract
    heavy_compute = """
    pragma solidity ^0.8.0;
    
    contract ComputeHeavy {
        function heavyComputation(uint256 x) public pure returns (uint256) {
            uint256 result = x;
            for (uint i = 0; i < 100; i++) {
                result = result * x + x / 2;
            }
            return result;
        }
    }
    """
    
    heavy_analyzer = EVMAnalyzer(heavy_compute)
    heavy_recs = heavy_analyzer.generate_recommendations()
    compute_heavy_recs = [r for r in heavy_recs if r.category == "computation"]
    
    assert len(compute_heavy_recs) > 0
    assert any(r.severity == "high" for r in compute_heavy_recs)

def test_invalid_contract_code():
    """Test analyzer behavior with invalid contract code."""
    with pytest.raises(Exception):
        analyzer = EVMAnalyzer("invalid code")
        analyzer.analyze()

def test_empty_contract():
    """Test analyzer behavior with empty contract."""
    analyzer = EVMAnalyzer("")
    metrics = analyzer.analyze()
    
    assert metrics.total_cost == 0
    assert metrics.bytecode_size == 0
    assert len(analyzer.generate_recommendations()) == 0 