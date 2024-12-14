# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "ipykernel",
# ]
# ///

import os
import sys
import json
import httpx
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List

class DataInsightProcessor:
    def __init__(self, file_path: str):
        self.input_file = file_path
        self.data_frame = pd.read_csv(file_path, encoding='latin-1')
        self.ml_generation_token = os.environ.get("AIPROXY_TOKEN")
        
        if not self.ml_generation_token:
            raise EnvironmentError("Machine learning generation token is not configured")
        
        self.inference_endpoint = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    def extract_dataset_characteristics(self) -> Dict[str, Any]:
        """
        Comprehensively analyze dataset structural characteristics
        """
        return {
            "dataset_profile": {
                "record_count": len(self.data_frame),
                "feature_names": list(self.data_frame.columns),
                "feature_types": {col: str(dtype) for col, dtype in self.data_frame.dtypes.items()},
                "missing_data": self.data_frame.isnull().sum().to_dict(),
                "initial_records": self.data_frame.head().to_dict()
            }
        }

    def create_visual_representations(self, output_directory: str):
        """
        Generate statistical visualizations for numeric features
        """
        os.makedirs(output_directory, exist_ok=True)
        
        plt.figure(figsize=(20, 10))
        
        # Correlation matrix visualization
        numeric_features = self.data_frame.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_features) > 1:
            plt.subplot(1, 2, 1)
            correlation_matrix = self.data_frame[numeric_features].corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
            plt.title('Feature Correlation Matrix')
            plt.tight_layout()
            plt.savefig(os.path.join(output_directory, 'feature_correlations.png'))
            plt.close()

        # Feature distribution plots
        plt.figure(figsize=(15, 5))
        active_numeric_features = [col for col in numeric_features if len(self.data_frame[col].dropna()) > 0]
        for i, feature in enumerate(active_numeric_features[:3], 1):
            plt.subplot(1, 3, i)
            sns.histplot(self.data_frame[feature].dropna(), kde=True)
            plt.title(f'Distribution: {feature}')
        plt.tight_layout()
        plt.savefig(os.path.join(output_directory, 'feature_distributions.png'))
        plt.close()

    def generate_narrative_summary(self, dataset_insights: Dict[str, Any]) -> str:
        """
        Utilize AI to generate a comprehensive narrative about the dataset
        """
        narrative_prompt = f"""
        Provide an in-depth narrative analysis of the dataset. Cover:
        1. Comprehensive dataset overview
        2. Significant statistical observations
        3. Potential insights and implications
        4. Formatted using Markdown

        Detailed Dataset Characteristics:
        {json.dumps(dataset_insights['dataset_profile'], indent=2)}
        """
    
        request_payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": narrative_prompt}]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ml_generation_token}"
        }

        try:
            print("Initiating narrative generation...")
            response = httpx.post(
                self.inference_endpoint, 
                headers=headers, 
                json=request_payload,
                timeout=httpx.Timeout(60.0)  # Set a 60-second timeout
            )
            
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            data = response.json()
            print("Narrative generation completed!")
            return data.get('choices', [{}])[0].get('message', {}).get('content', 'No narrative generated')

        except httpx.TimeoutException:
            print("Timeout occurred during narrative generation")
            return "Narrative generation timed out after 60 seconds"
        
        except httpx.HTTPStatusError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return f"HTTP Error: {http_err}"
        
        except Exception as processing_error:
            print("Narrative generation encountered an issue!")
            print(f"Error details: {processing_error}")
            return "Narrative generation unsuccessful"

    def execute_analysis(self):
        """
        Orchestrate complete dataset analysis workflow
        """
        # Derive output directory from input filename
        output_directory = os.path.splitext(os.path.basename(self.input_file))[0]
        os.makedirs(output_directory, exist_ok=True)
        
        # Analyze dataset characteristics
        dataset_insights = self.extract_dataset_characteristics()
        
        # Generate visualizations
        self.create_visual_representations(output_directory)
        
        # Generate narrative summary
        narrative_content = self.generate_narrative_summary(dataset_insights)
        
        # Write narrative to README
        with open(os.path.join(output_directory, 'README.md'), 'w', encoding='utf-8') as narrative_file:
            narrative_file.write(narrative_content)

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)
    
    dataset_path = sys.argv[1]
    insight_processor = DataInsightProcessor(dataset_path)
    insight_processor.execute_analysis()

if __name__ == "__main__":
    main()
