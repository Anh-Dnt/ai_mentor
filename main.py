import os
import datetime
from dotenv import load_dotenv
import json

# Các thư viện của Google để xác thực và tương tác với Calendar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Các thư viện của LangChain để xây dựng Agent
from langchain.agents import Tool, create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Tải các biến môi trường từ file .env
load_dotenv()

# --- PHẦN 1: CÔNG CỤ ĐỌC LỊCH (PHIÊN BẢN CHO MÁY LOCAL) ---

# Định nghĩa phạm vi truy cập vào Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"  # File này sẽ được tự động tạo ra
FLASHCARDS_FILE = "flashcards.json"

# Công cụ đọc lịch từ Google Calendar
def get_calendar_events(days_to_check_str: str) -> str:
    """
    Công cụ để kiểm tra các sự kiện trên Google Calendar.
    Đầu vào là một chuỗi ký tự chứa số ngày cần kiểm tra trong tương lai.
    """
    creds = None
    # File token.json lưu trữ token của người dùng sau lần đăng nhập đầu tiên
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # Nếu không có credentials hợp lệ, yêu cầu người dùng đăng nhập
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Dòng này sẽ tự động mở trình duyệt để bạn đăng nhập và cấp quyền
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Lưu credentials cho những lần chạy sau
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    try:
        # Chuyển đổi đầu vào từ chuỗi sang số
        days_to_check = int(days_to_check_str)
        service = build("calendar", "v3", credentials=creds)

        # Lấy thời gian hiện tại và tính thời gian kết thúc
        now = datetime.datetime.utcnow().isoformat() + "Z"
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=days_to_check)).isoformat() + "Z"

        # Gọi Google Calendar API
        events_result = service.events().list(
            calendarId="primary", timeMin=now, timeMax=end_date,
            maxResults=15, singleEvents=True, orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        if not events:
            return "Không tìm thấy sự kiện nào trong lịch của bạn."

        event_list = "Đây là các sự kiện sắp tới của bạn:\n"
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
            event_list += f"- {start_dt.strftime('%A, %d/%m/%Y lúc %H:%M')}: {event['summary']}\n"
        
        return event_list
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

# CÔNG CỤ TÌM KIẾM TÀI LIỆU HỌC TẬP
def search_study_materials(query: str) -> str:
    """
    Công cụ tìm kiếm tài liệu học tập trực tuyến.
    Rất hữu ích để tìm các bài giảng, video, hoặc bài viết về một chủ đề cụ thể.
    """
    try:
        api_key = os.getenv("CUSTOM_SEARCH_API_KEY")
        search_engine_id = os.getenv("SEARCH_ENGINE_ID")

        # Xây dựng dịch vụ tìm kiếm
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Thực hiện tìm kiếm
        result = service.cse().list(q=query, cx=search_engine_id, num=3).execute()
        
        if "items" not in result:
            return "Không tìm thấy tài liệu nào phù hợp."

        # Định dạng kết quả
        search_results = f"Đây là một vài tài liệu hữu ích cho chủ đề '{query}':\n"
        for item in result["items"]:
            search_results += f"- Tiêu đề: {item['title']}\n"
            search_results += f"  Link: {item['link']}\n"
            search_results += f"  Mô tả: {item.get('snippet', 'Không có mô tả.')}\n\n"
        
        return search_results

    except HttpError as e:
        # Xử lý lỗi nếu API key hoặc Search Engine ID sai
        if e.resp.status == 400 or e.resp.status == 403:
            return "Lỗi: API Key hoặc Search Engine ID không hợp lệ. Vui lòng kiểm tra lại file .env."
        return f"Đã xảy ra lỗi khi tìm kiếm: {e}"
    except Exception as e:
        return f"Đã xảy ra một lỗi không xác định: {e}"

# CÔNG CỤ QUẢN LÝ THẺ GHI NHỚ ---
def manage_flashcards(action: str, topic: str = "", front: str = "", back: str = "") -> str:
    """
    Công cụ để quản lý thẻ ghi nhớ (flashcards). 
    Các hành động (action) bao gồm: 'add' (thêm thẻ), 'get' (lấy thẻ theo chủ đề), và 'list_topics' (liệt kê các chủ đề).
    - Để 'add': cần có 'topic', 'front', và 'back'.
    - Để 'get': chỉ cần 'topic'.
    - Để 'list_topics': không cần tham số khác.
    """
    # Đọc dữ liệu thẻ ghi nhớ hiện có
    if os.path.exists(FLASHCARDS_FILE):
        with open(FLASHCARDS_FILE, 'r', encoding='utf-8') as f:
            flashcards = json.load(f)
    else:
        flashcards = {}

    # Xử lý các hành động
    if action == "add":
        if not all([topic, front, back]):
            return "Lỗi: Để thêm thẻ, cần cung cấp đủ topic, front, và back."
        
        if topic not in flashcards:
            flashcards[topic] = []
        
        flashcards[topic].append({"front": front, "back": back})
        
        # Lưu lại vào file
        with open(FLASHCARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, ensure_ascii=False, indent=4)
        return f"Đã thêm thành công thẻ ghi nhớ vào chủ đề '{topic}'."

    elif action == "get":
        if not topic:
            return "Lỗi: Cần cung cấp topic để lấy thẻ ghi nhớ."
        
        cards = flashcards.get(topic)
        if not cards:
            return f"Không tìm thấy thẻ ghi nhớ nào cho chủ đề '{topic}'."
        
        response = f"Các thẻ ghi nhớ cho chủ đề '{topic}':\n"
        for i, card in enumerate(cards, 1):
            response += f"{i}. Mặt trước: {card['front']} | Mặt sau: {card['back']}\n"
        return response

    elif action == "list_topics":
        if not flashcards:
            return "Bạn chưa có chủ đề thẻ ghi nhớ nào."
        
        topics = list(flashcards.keys())
        return f"Các chủ đề thẻ ghi nhớ bạn đang có: {', '.join(topics)}"

    else:
        return f"Lỗi: Hành động '{action}' không được hỗ trợ. Chỉ có thể dùng 'add', 'get', 'list_topics'."

# --- PHẦN 2: THIẾT LẬP VÀ CHẠY AGENT ---

def main():
    """Hàm chính để thiết lập và chạy vòng lặp tương tác với AI Mentor."""
    
    print("🤖 Khởi tạo AI Mentor...")

    # 1. Tạo Tool
    # Công cụ đọc lịch từ Google Calendar
    calendar_tool = Tool(
        name="Google_Calendar_Reader",
        func=get_calendar_events,
        description="Rất hữu ích để tìm hiểu về các sự kiện, kỳ thi, hoặc hạn chót sắp tới từ Google Calendar. Đầu vào của công cụ này là một con số, đại diện cho số ngày cần kiểm tra trong tương lai.",
    )
    # Công cụ tìm kiếm tài liệu học tập
    search_tool = Tool(
        name="Study_Material_Searcher",
        func=search_study_materials,
        description="Rất hữu ích để tìm các bài giảng, video, hoặc bài viết về một chủ đề học tập cụ thể. Ví dụ đầu vào: 'bài giảng về tích phân lớp 12'.",
    )
    # Công cụ quản lý thẻ ghi nhớ
    flashcard_tool = Tool(
    name="Flashcard_Manager",
    # Lambda function này sẽ tìm và trích xuất phần JSON cốt lõi trước khi xử lý
    func=lambda params: manage_flashcards(**json.loads(params[params.find('{') : params.rfind('}')+1])),
    description="""Công cụ để quản lý thẻ ghi nhớ. Hữu ích để thêm, xem lại, hoặc liệt kê các thẻ ghi nhớ.
        Đầu vào PHẢI là một chuỗi JSON hợp lệ.
        Ví dụ:
        - Để thêm thẻ: {"action": "add", "topic": "Tên chủ đề", "front": "Nội dung mặt trước", "back": "Nội dung mặt sau"}
        - Để xem thẻ: {"action": "get", "topic": "Tên chủ đề"}
        - Để liệt kê chủ đề: {"action": "list_topics"}
        """,
    )
    
    # Danh sách các công cụ
    tools = [calendar_tool, search_tool, flashcard_tool]

    # 2. Tạo Prompt Template
    prompt_template = """
    Bạn là AI Mentor, một trợ lý học tập thông minh. Mục tiêu của bạn là trả lời câu hỏi của người dùng bằng tiếng Việt.
    Bạn có quyền truy cập vào các công cụ sau đây: {tools}
    Để sử dụng một công cụ, bạn PHẢI tuân thủ nghiêm ngặt định dạng sau:
    ```
    Thought: Suy nghĩ của bạn về việc có cần sử dụng công cụ hay không.
    Action: Tên của công cụ cần dùng, PHẢI là MỘT trong các tên sau: {tool_names}.
    Action Input: Đầu vào cho công cụ.
    Observation: Kết quả trả về từ công cụ.
    ```
    Khi bạn đã có đủ thông tin, hãy dùng định dạng sau:
    ```
    Thought: Bây giờ tôi đã có đủ thông tin để đưa ra câu trả lời cuối cùng.
    Final Answer: [Câu trả lời cuối cùng của bạn ở đây]
    ```
    Bắt đầu nào!
    Question: {input}
    Thought: {agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(template=prompt_template)

    # 3. Thiết lập LLM và Agent
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print("✅ AI Mentor đã sẵn sàng! Gõ 'quit' để thoát.")
    
    # 4. Tạo vòng lặp tương tác
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() == 'quit':
            print("👋 Tạm biệt!")
            break
        
        response = agent_executor.invoke({"input": user_input})
        print(f"AI Mentor: {response['output']}")

if __name__ == "__main__":
    main()