import os
import json


def main():
    # ================= Configuration =================
    # Directory containing model performance results
    input_dir = 'model_performance'

    # Directory to save the new task performance JSONs
    output_dir = 'task_performance'
    # ===============================================

    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    datasets_data = {}

    print(f"Reading model data from '{input_dir}' directory, starting dimension conversion...")

    file_count = 0
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
        except Exception as e:
            print(f"  [Skip] Failed to read file {filename}: {e}")
            continue

        file_count += 1

        # 1. Extract the global info of the current model
        model_info = model_data.get("info", {})

        # Extract the model name to use as a key under the dataset's performance dictionary
        model_name_key = filename.replace("_performance.json", "")
        model_performance = model_data.get("performance", {})

        # 2. Iterate through all datasets the model participated in
        for dataset_name, ds_content in model_performance.items():
            if dataset_name not in datasets_data:
                # If encountering this dataset for the first time, initialize its top-level structure.
                # Extract the dataset's own feature information into the top-level "info".
                datasets_data[dataset_name] = {
                    "info": ds_content.get("dataset", {}),
                    "performance": {}
                }

            # 3. Mount the model's metrics under the dataset's performance field
            datasets_data[dataset_name]["performance"][model_name_key] = {
                "model": model_info,
                "parameters": ds_content.get("parameters", {}),
                "performance": ds_content.get("performance", {})
            }

    print(f"Read {file_count} model files, found {len(datasets_data)} independent datasets after aggregation.")
    print("Generating task performance reports based on datasets...")

    # ================= Save JSON files =================
    saved_count = 0
    for dataset_name, ds_data in datasets_data.items():
        # Clean up invalid characters that might cause path errors
        safe_dataset_name = str(dataset_name).replace("/", "_").replace("\\", "_")

        out_file = os.path.join(output_dir, f"{safe_dataset_name}_task_performance.json")
        with open(out_file, "w", encoding='utf-8') as f:
            json.dump(ds_data, f, indent=4, ensure_ascii=False)
        saved_count += 1

    print("\n✅ Dimension conversion completed!")
    print(f"✅ Successfully generated {saved_count} dataset-level JSON files.")
    print(f"✅ All files have been saved in the directory: {output_dir}/")


if __name__ == "__main__":
    main()
