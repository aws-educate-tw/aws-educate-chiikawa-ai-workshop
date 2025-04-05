import os
import re

def split_markdown_file(input_file, max_size_mb=50, output_dir=None, output_prefix=None):
    """
    將大型 Markdown 檔案分割成多個小於指定大小的檔案
    
    參數:
        input_file (str): 輸入檔案的路徑
        max_size_mb (int): 每個輸出檔案的最大大小 (MB)
        output_dir (str): 輸出目錄，如果為 None，則使用輸入檔案的目錄
        output_prefix (str): 輸出檔案的前綴，如果為 None，則使用輸入檔案名
    
    返回:
        list: 已創建的檔案列表
    """
    # 轉換 MB 到位元組
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # 設定輸出目錄和前綴
    if output_dir is None:
        output_dir = os.path.dirname(input_file)
    if output_dir == '':
        output_dir = '.'
    
    if output_prefix is None:
        output_prefix = os.path.basename(input_file)
        # 移除副檔名
        if '.' in output_prefix:
            output_prefix = output_prefix.rsplit('.', 1)[0]
    
    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 讀取檔案
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 通過 Markdown 標題分割內容
    # 尋找所有 h1-h6 標題
    headers = re.finditer(r'^(#{1,6}\s.+)$', content, re.MULTILINE)
    
    # 獲取所有標題的位置
    split_positions = [0]  # 起始位置
    
    for match in headers:
        split_positions.append(match.start())
    
    split_positions.append(len(content))  # 結束位置
    
    # 分割文件
    created_files = []
    part_num = 1
    current_part = ""
    current_size = 0
    
    for i in range(1, len(split_positions)):
        section_start = split_positions[i-1]
        section_end = split_positions[i] if i < len(split_positions) - 1 else len(content)
        section = content[section_start:section_end]
        
        section_size = len(section.encode('utf-8'))  # 獲取實際位元組大小
        
        # 如果新片段太大，自行分割為更小的部分
        if section_size > max_size_bytes:
            # 以段落為單位分割
            paragraphs = re.split(r'\n\s*\n', section)
            for paragraph in paragraphs:
                para_size = len(paragraph.encode('utf-8'))
                
                # 檢查加入這個段落是否會超過檔案大小限制
                if current_size + para_size > max_size_bytes:
                    # 儲存當前部分並開始新的部分
                    output_file = os.path.join(output_dir, f"{output_prefix}_part{part_num}.md")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(current_part)
                    created_files.append(output_file)
                    
                    part_num += 1
                    current_part = paragraph + "\n\n"
                    current_size = para_size
                else:
                    current_part += paragraph + "\n\n"
                    current_size += para_size
        else:
            # 檢查加入這個區塊是否會超過檔案大小限制
            if current_size + section_size > max_size_bytes and current_size > 0:
                # 儲存當前部分並開始新的部分
                output_file = os.path.join(output_dir, f"{output_prefix}_part{part_num}.md")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(current_part)
                created_files.append(output_file)
                
                part_num += 1
                current_part = section
                current_size = section_size
            else:
                current_part += section
                current_size += section_size
    
    # 儲存最後一部分
    if current_size > 0:
        output_file = os.path.join(output_dir, f"{output_prefix}_part{part_num}.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(current_part)
        created_files.append(output_file)
    
    # 輸出結果
    print(f"原始檔案大小: {os.path.getsize(input_file) / (1024*1024):.2f} MB")
    print(f"已分割為 {len(created_files)} 個檔案:")
    
    for file in created_files:
        print(f"  - {os.path.basename(file)}: {os.path.getsize(file) / (1024*1024):.2f} MB")
    
    return created_files

# 使用方式範例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='將大型 Markdown 檔案分割成多個小檔案')
    parser.add_argument('input_file', help='輸入 Markdown 檔案的路徑')
    parser.add_argument('--max-size', type=int, default=50, help='每個輸出檔案的最大大小 (MB)，預設為 50MB')
    parser.add_argument('--output-dir', help='輸出目錄，預設為輸入檔案的目錄')
    parser.add_argument('--output-prefix', help='輸出檔案的前綴，預設為輸入檔案名')
    
    args = parser.parse_args()
    
    split_markdown_file(
        args.input_file,
        max_size_mb=args.max_size,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix
    )