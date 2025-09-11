#!/usr/bin/env python3
"""
Test script to verify Darwin retriever date filtering functionality.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from retrievers.darwin_retriever import DarwinRetriever

def test_date_filtering():
    """Test the new date filtering options."""
    print("Testing Darwin retriever date filtering...")
    
    # Initialize retriever
    retriever = DarwinRetriever()
    
    # Test the new time period options
    print("\nAvailable time period options:")
    for option in retriever.get_time_period_options():
        print(f"  - {option['value']}: {option['label']}")
    
    # Test queries with different date filters
    test_query = "species evolution"
    
    date_filters = ["all", "before-1860", "1860-1870", "1870-1882"]
    
    for date_filter in date_filters:
        print(f"\n--- Testing filter: {date_filter} ---")
        try:
            # Use similar_search method to test filtering
            results = retriever.similar_search(
                query=test_query, 
                k=5, 
                time_period_filter=date_filter
            )
            
            print(f"Found {len(results)} results")
            
            # Show years found in results
            years_found = set()
            for result in results:
                year = result.get('year')
                if year and year != 'unknown':
                    years_found.add(year)
            
            if years_found:
                print(f"Years in results: {sorted(years_found)}")
            else:
                print("No year information found in results")
                
        except Exception as e:
            print(f"Error testing filter {date_filter}: {e}")
    
    print("\n✅ Date filtering test completed!")

if __name__ == "__main__":
    test_date_filtering()