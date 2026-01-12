"""
patient_gui.py
환자 정보 관리 시스템 GUI

Author: KDT12 Python Project
Date: 2026-01-09
"""

from tkinter import *
from tkinter import ttk, messagebox
from .patient import Patient
from .patient_manager import PatientManager


class PatientManagementApp(Toplevel):
    """환자 정보 관리 GUI (Toplevel 기반)"""
    
    def __init__(self, parent=None, base_path=None):
        """생성자"""
        super().__init__(parent)
        
        self.title("📋 환자 정보 관리 시스템")
        self.geometry("1100x700")
        self.resizable(True, True)
        self.minsize(900, 600)
        
        # 색상 테마
        self.colors = {
            "bg": "#f0f4f8",
            "header": "#9b59b6",
            "primary": "#3498db",
            "success": "#27ae60",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "dark": "#2c3e50",
            "light": "#ecf0f1",
            "white": "#ffffff"
        }
        
        self.configure(bg=self.colors["bg"])
        
        # 데이터 매니저 초기화
        try:
            self.manager = PatientManager(base_path)
        except Exception as e:
            print(f"[PatientManagementApp] 매니저 초기화 오류: {e}")
            self.manager = None
        
        # 연동 매니저 초기화 (건강 체크 시스템 연동)
        self.integration_manager = None
        self._init_integration(base_path)
        
        # 위젯 생성
        self.create_widgets()
        
        # 테이블 새로고침
        self.refresh_table()
        
        # 창 닫기 이벤트
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """창 닫기"""
        self.destroy()
    
    def create_widgets(self):
        """모든 위젯 생성"""
        # 헤더
        header = Frame(self, bg=self.colors["header"], height=60)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        Label(
            header,
            text="📋 환자 정보 관리 시스템 (CRUD)",
            font=("맑은 고딕", 16, "bold"),
            fg=self.colors["white"],
            bg=self.colors["header"]
        ).pack(side=LEFT, padx=20, pady=15)
        
        Button(
            header,
            text="✕ 닫기",
            font=("맑은 고딕", 10),
            bg=self.colors["header"],
            fg=self.colors["white"],
            relief=FLAT,
            cursor="hand2",
            command=self.on_close
        ).pack(side=RIGHT, padx=20)
        
        # 검색바
        search_frame = Frame(self, bg=self.colors["bg"], pady=10)
        search_frame.pack(fill=X, padx=20)
        
        Label(search_frame, text="🔍 검색:", font=("맑은 고딕", 11), bg=self.colors["bg"]).pack(side=LEFT)
        
        self.search_entry = Entry(search_frame, font=("맑은 고딕", 11), width=30)
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_patients())
        
        self.search_field = StringVar(value="all")
        field_combo = ttk.Combobox(
            search_frame,
            textvariable=self.search_field,
            values=["all", "name", "medical_condition", "doctor", "hospital"],
            width=15,
            state="readonly"
        )
        field_combo.pack(side=LEFT, padx=5)
        
        Button(
            search_frame, text="검색", font=("맑은 고딕", 10),
            bg=self.colors["primary"], fg=self.colors["white"],
            relief=FLAT, command=self.search_patients
        ).pack(side=LEFT, padx=5, ipadx=10)
        
        Button(
            search_frame, text="초기화", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=self.reset_search
        ).pack(side=LEFT, padx=5, ipadx=10)
        
        # 테이블
        table_frame = Frame(self, bg=self.colors["bg"])
        table_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        y_scroll = Scrollbar(table_frame, orient=VERTICAL)
        y_scroll.pack(side=RIGHT, fill=Y)
        
        x_scroll = Scrollbar(table_frame, orient=HORIZONTAL)
        x_scroll.pack(side=BOTTOM, fill=X)
        
        columns = (
            "patient_id", "name", "age", "gender", "blood_type",
            "medical_condition", "doctor", "hospital", "room_number",
            "admission_type", "test_results", "billing_amount"
        )
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            height=18
        )
        
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)
        
        column_configs = {
            "patient_id": ("ID", 60),
            "name": ("이름", 80),
            "age": ("나이", 50),
            "gender": ("성별", 50),
            "blood_type": ("혈액형", 60),
            "medical_condition": ("진단명", 100),
            "doctor": ("담당의", 100),
            "hospital": ("병원", 120),
            "room_number": ("병실", 50),
            "admission_type": ("입원유형", 80),
            "test_results": ("검사결과", 80),
            "billing_amount": ("청구금액", 100)
        }
        
        for col, (heading, width) in column_configs.items():
            self.tree.heading(col, text=heading, anchor=CENTER)
            self.tree.column(col, width=width, anchor=CENTER)
        
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda e: self.show_detail_dialog())
        
        # 버튼 영역
        btn_frame = Frame(self, bg=self.colors["bg"], pady=10)
        btn_frame.pack(fill=X, padx=20)
        
        # 버튼 생성 - command를 lambda로 감싸서 연결
        Button(
            btn_frame, text="➕ 환자 등록", font=("맑은 고딕", 10),
            bg=self.colors["success"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.show_create_dialog()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="📝 정보 수정", font=("맑은 고딕", 10),
            bg=self.colors["warning"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.show_update_dialog()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="🗑️ 삭제", font=("맑은 고딕", 10),
            bg=self.colors["danger"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.delete_selected()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="📋 상세보기", font=("맑은 고딕", 10),
            bg=self.colors["primary"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.show_detail_dialog()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="🏥 퇴원처리", font=("맑은 고딕", 10),
            bg="#9b59b6", fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.discharge_patient()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="💓 건강기록", font=("맑은 고딕", 10),
            bg="#27ae60", fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.show_health_records()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="🩺 건강체크", font=("맑은 고딕", 10),
            bg="#16a085", fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.start_health_check()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="📊 통계", font=("맑은 고딕", 10),
            bg=self.colors["dark"], fg=self.colors["white"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.show_statistics()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        Button(
            btn_frame, text="🔄 새로고침", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, cursor="hand2",
            command=lambda: self.refresh_table()
        ).pack(side=LEFT, padx=5, ipadx=10, ipady=5)
        
        # 상태바
        self.status_frame = Frame(self, bg=self.colors["header"], height=30)
        self.status_frame.pack(fill=X, side=BOTTOM)
        self.status_frame.pack_propagate(False)
        
        self.status_label = Label(
            self.status_frame, text="", font=("맑은 고딕", 9),
            fg=self.colors["light"], bg=self.colors["header"]
        )
        self.status_label.pack(side=LEFT, padx=20)
        
        self.update_status_bar()
    
    def update_status_bar(self):
        """상태바 업데이트"""
        if not self.manager:
            self.status_label.config(text="⚠️ 데이터 로드 실패")
            return
        
        total = len(self.manager.patients)
        hospitalized = sum(1 for p in self.manager.patients if p.is_hospitalized())
        today = self.manager.get_today_admissions()
        
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.status_label.config(
            text=f"총 환자: {total}명 | 입원 중: {hospitalized}명 | 오늘 입원: {today}명 | 마지막 업데이트: {current_time}"
        )
    
    def refresh_table(self, patients=None):
        """테이블 새로고침"""
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.manager:
            return
        
        if patients is None:
            self.manager.load_from_file()
            patients = self.manager.read_all()
        
        for patient in patients:
            values = (
                patient.patient_id,
                patient.name,
                patient.age,
                patient.get_gender_korean(),
                patient.blood_type,
                patient.medical_condition,
                patient.doctor,
                patient.hospital,
                patient.room_number if patient.room_number else "-",
                patient.get_admission_type_korean(),
                patient.get_test_results_korean(),
                patient.get_billing_formatted()
            )
            self.tree.insert("", END, values=values)
        
        self.update_status_bar()
    
    def get_selected_patient_id(self):
        """선택된 환자 ID 반환 (문자열로 변환)"""
        selected = self.tree.selection()
        if not selected:
            return None
        item = self.tree.item(selected[0])
        values = item.get("values", [])
        if values:
            # 명시적으로 문자열로 변환
            return str(values[0])
        return None
    
    def search_patients(self):
        """환자 검색"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        keyword = self.search_entry.get().strip()
        field = self.search_field.get()
        
        if not keyword:
            self.refresh_table()
            return
        
        results = self.manager.search(keyword, field)
        self.refresh_table(results)
        messagebox.showinfo("검색 결과", f"{len(results)}명의 환자를 찾았습니다.")
    
    def reset_search(self):
        """검색 초기화"""
        self.search_entry.delete(0, END)
        self.search_field.set("all")
        self.refresh_table()
    
    def show_create_dialog(self):
        """환자 등록 다이얼로그"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        dialog = Toplevel(self)
        dialog.title("➕ 새 환자 등록")
        dialog.geometry("450x620")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self)
        dialog.grab_set()
        
        # 제목
        Label(
            dialog, text="➕ 새 환자 등록",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        # 폼 프레임
        form_frame = Frame(dialog, bg=self.colors["white"])
        form_frame.pack(fill=X, padx=30)
        
        entries = {}
        
        # 기본 정보
        Label(
            form_frame, text="─── 기본 정보 ───",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["white"]
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky=W)
        
        # 이름
        Label(form_frame, text="이름:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=1, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["name"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["name"].grid(row=1, column=1, pady=5, sticky=W)
        
        # 나이
        Label(form_frame, text="나이:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=2, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["age"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["age"].grid(row=2, column=1, pady=5, sticky=W)
        
        # 성별
        Label(form_frame, text="성별:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=3, column=0, pady=5, sticky=E, padx=(0, 10))
        gender_var = StringVar(value="Male")
        gender_frame = Frame(form_frame, bg=self.colors["white"])
        gender_frame.grid(row=3, column=1, pady=5, sticky=W)
        Radiobutton(gender_frame, text="남성", variable=gender_var, value="Male", bg=self.colors["white"]).pack(side=LEFT)
        Radiobutton(gender_frame, text="여성", variable=gender_var, value="Female", bg=self.colors["white"]).pack(side=LEFT)
        entries["gender"] = gender_var
        
        # 혈액형
        Label(form_frame, text="혈액형:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=4, column=0, pady=5, sticky=E, padx=(0, 10))
        blood_var = StringVar(value="A+")
        ttk.Combobox(form_frame, textvariable=blood_var, values=Patient.VALID_BLOOD_TYPES, width=22, state="readonly").grid(row=4, column=1, pady=5, sticky=W)
        entries["blood_type"] = blood_var
        
        # 의료 정보
        Label(
            form_frame, text="─── 의료 정보 ───",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["white"]
        ).grid(row=5, column=0, columnspan=2, pady=(15, 5), sticky=W)
        
        # 진단명
        Label(form_frame, text="진단명:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=6, column=0, pady=5, sticky=E, padx=(0, 10))
        condition_var = StringVar(value="Diabetes")
        ttk.Combobox(form_frame, textvariable=condition_var, values=Patient.VALID_CONDITIONS, width=22, state="readonly").grid(row=6, column=1, pady=5, sticky=W)
        entries["medical_condition"] = condition_var
        
        # 담당의
        Label(form_frame, text="담당의:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=7, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["doctor"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["doctor"].grid(row=7, column=1, pady=5, sticky=W)
        
        # 병원
        Label(form_frame, text="병원:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=8, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["hospital"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["hospital"].grid(row=8, column=1, pady=5, sticky=W)
        
        # 병실
        Label(form_frame, text="병실:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=9, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["room_number"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["room_number"].grid(row=9, column=1, pady=5, sticky=W)
        
        # 입원유형
        Label(form_frame, text="입원유형:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=10, column=0, pady=5, sticky=E, padx=(0, 10))
        admission_var = StringVar(value="Elective")
        ttk.Combobox(form_frame, textvariable=admission_var, values=Patient.VALID_ADMISSION_TYPES, width=22, state="readonly").grid(row=10, column=1, pady=5, sticky=W)
        entries["admission_type"] = admission_var
        
        # 기타 정보
        Label(
            form_frame, text="─── 기타 정보 ───",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["white"]
        ).grid(row=11, column=0, columnspan=2, pady=(15, 5), sticky=W)
        
        # 보험사
        Label(form_frame, text="보험사:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=12, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["insurance_provider"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["insurance_provider"].grid(row=12, column=1, pady=5, sticky=W)
        
        # 처방약
        Label(form_frame, text="처방약:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=13, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["medication"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["medication"].grid(row=13, column=1, pady=5, sticky=W)
        
        # 청구금액
        Label(form_frame, text="청구금액:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=14, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["billing_amount"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["billing_amount"].grid(row=14, column=1, pady=5, sticky=W)
        
        # 검사결과
        Label(form_frame, text="검사결과:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=15, column=0, pady=5, sticky=E, padx=(0, 10))
        test_var = StringVar(value="Normal")
        ttk.Combobox(form_frame, textvariable=test_var, values=Patient.VALID_TEST_RESULTS, width=22, state="readonly").grid(row=15, column=1, pady=5, sticky=W)
        entries["test_results"] = test_var
        
        # 저장 함수
        def save_patient():
            try:
                name = entries["name"].get().strip()
                age_str = entries["age"].get().strip()
                
                if not name:
                    messagebox.showerror("입력 오류", "이름을 입력하세요.")
                    return
                
                if not age_str:
                    messagebox.showerror("입력 오류", "나이를 입력하세요.")
                    return
                
                data = {
                    "name": name,
                    "age": int(age_str),
                    "gender": entries["gender"].get(),
                    "blood_type": entries["blood_type"].get(),
                    "medical_condition": entries["medical_condition"].get(),
                    "doctor": entries["doctor"].get().strip(),
                    "hospital": entries["hospital"].get().strip(),
                    "room_number": int(entries["room_number"].get()) if entries["room_number"].get().strip() else 0,
                    "admission_type": entries["admission_type"].get(),
                    "insurance_provider": entries["insurance_provider"].get().strip(),
                    "medication": entries["medication"].get().strip(),
                    "billing_amount": float(entries["billing_amount"].get()) if entries["billing_amount"].get().strip() else 0,
                    "test_results": entries["test_results"].get()
                }
                
                success, result = self.manager.create(data)
                
                if success:
                    messagebox.showinfo("등록 완료", f"환자가 등록되었습니다.\n환자 ID: {result}")
                    dialog.destroy()
                    self.refresh_table()
                else:
                    messagebox.showerror("등록 실패", result)
            except ValueError as e:
                messagebox.showerror("입력 오류", f"숫자 필드에 올바른 값을 입력하세요.\n{str(e)}")
            except Exception as e:
                messagebox.showerror("오류", f"등록 중 오류가 발생했습니다.\n{str(e)}")
        
        # 버튼 프레임
        btn_frame = Frame(dialog, bg=self.colors["white"])
        btn_frame.pack(pady=20)
        
        Button(
            btn_frame, text="등록", font=("맑은 고딕", 11),
            bg=self.colors["success"], fg=self.colors["white"],
            relief=FLAT, command=save_patient
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
        
        Button(
            btn_frame, text="취소", font=("맑은 고딕", 11),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=dialog.destroy
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
    
    def show_update_dialog(self):
        """환자 수정 다이얼로그"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "수정할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", f"환자 정보를 찾을 수 없습니다. (ID: {patient_id})")
            return
        
        dialog = Toplevel(self)
        dialog.title(f"📝 환자 정보 수정 - {patient_id}")
        dialog.geometry("450x550")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self)
        dialog.grab_set()
        
        Label(
            dialog, text=f"📝 환자 정보 수정 ({patient_id})",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        form_frame = Frame(dialog, bg=self.colors["white"])
        form_frame.pack(fill=X, padx=30)
        
        entries = {}
        
        # 이름
        Label(form_frame, text="이름:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=0, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["name"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["name"].insert(0, patient.name)
        entries["name"].grid(row=0, column=1, pady=5, sticky=W)
        
        # 나이
        Label(form_frame, text="나이:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=1, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["age"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["age"].insert(0, str(patient.age))
        entries["age"].grid(row=1, column=1, pady=5, sticky=W)
        
        # 진단명
        Label(form_frame, text="진단명:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=2, column=0, pady=5, sticky=E, padx=(0, 10))
        condition_var = StringVar(value=patient.medical_condition)
        ttk.Combobox(form_frame, textvariable=condition_var, values=Patient.VALID_CONDITIONS, width=22, state="readonly").grid(row=2, column=1, pady=5, sticky=W)
        entries["medical_condition"] = condition_var
        
        # 담당의
        Label(form_frame, text="담당의:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=3, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["doctor"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["doctor"].insert(0, patient.doctor)
        entries["doctor"].grid(row=3, column=1, pady=5, sticky=W)
        
        # 병원
        Label(form_frame, text="병원:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=4, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["hospital"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["hospital"].insert(0, patient.hospital)
        entries["hospital"].grid(row=4, column=1, pady=5, sticky=W)
        
        # 병실
        Label(form_frame, text="병실:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=5, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["room_number"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["room_number"].insert(0, str(patient.room_number) if patient.room_number else "")
        entries["room_number"].grid(row=5, column=1, pady=5, sticky=W)
        
        # 처방약
        Label(form_frame, text="처방약:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=6, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["medication"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["medication"].insert(0, patient.medication if patient.medication else "")
        entries["medication"].grid(row=6, column=1, pady=5, sticky=W)
        
        # 검사결과
        Label(form_frame, text="검사결과:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=7, column=0, pady=5, sticky=E, padx=(0, 10))
        test_var = StringVar(value=patient.test_results)
        ttk.Combobox(form_frame, textvariable=test_var, values=Patient.VALID_TEST_RESULTS, width=22, state="readonly").grid(row=7, column=1, pady=5, sticky=W)
        entries["test_results"] = test_var
        
        # 청구금액
        Label(form_frame, text="청구금액:", font=("맑은 고딕", 10), bg=self.colors["white"]).grid(row=8, column=0, pady=5, sticky=E, padx=(0, 10))
        entries["billing_amount"] = Entry(form_frame, font=("맑은 고딕", 10), width=25)
        entries["billing_amount"].insert(0, str(int(patient.billing_amount)))
        entries["billing_amount"].grid(row=8, column=1, pady=5, sticky=W)
        
        # 수정 함수
        def update_patient():
            try:
                data = {
                    "name": entries["name"].get().strip(),
                    "age": int(entries["age"].get()) if entries["age"].get().strip() else 0,
                    "medical_condition": entries["medical_condition"].get(),
                    "doctor": entries["doctor"].get().strip(),
                    "hospital": entries["hospital"].get().strip(),
                    "room_number": int(entries["room_number"].get()) if entries["room_number"].get().strip() else 0,
                    "medication": entries["medication"].get().strip(),
                    "test_results": entries["test_results"].get(),
                    "billing_amount": float(entries["billing_amount"].get()) if entries["billing_amount"].get().strip() else 0
                }
                
                success, msg = self.manager.update(patient_id, data)
                
                if success:
                    messagebox.showinfo("수정 완료", msg)
                    dialog.destroy()
                    self.refresh_table()
                else:
                    messagebox.showerror("수정 실패", msg)
            except ValueError as e:
                messagebox.showerror("입력 오류", f"숫자 필드에 올바른 값을 입력하세요.\n{str(e)}")
            except Exception as e:
                messagebox.showerror("오류", f"수정 중 오류가 발생했습니다.\n{str(e)}")
        
        btn_frame = Frame(dialog, bg=self.colors["white"])
        btn_frame.pack(pady=20)
        
        Button(
            btn_frame, text="수정", font=("맑은 고딕", 11),
            bg=self.colors["warning"], fg=self.colors["white"],
            relief=FLAT, command=update_patient
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
        
        Button(
            btn_frame, text="취소", font=("맑은 고딕", 11),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=dialog.destroy
        ).pack(side=LEFT, padx=10, ipadx=20, ipady=5)
    
    def show_detail_dialog(self):
        """상세 정보 다이얼로그"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "조회할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", f"환자 정보를 찾을 수 없습니다. (ID: {patient_id})")
            return
        
        dialog = Toplevel(self)
        dialog.title(f"📋 환자 상세 정보 - {patient_id}")
        dialog.geometry("400x520")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self)
        
        # 헤더
        header_frame = Frame(dialog, bg=self.colors["header"], pady=15)
        header_frame.pack(fill=X)
        
        status_icon = "🏥" if patient.is_hospitalized() else "✅"
        status_text = "입원중" if patient.is_hospitalized() else "퇴원"
        
        Label(
            header_frame,
            text=f"👤 {patient.name} ({patient.age}세, {patient.get_gender_korean()})",
            font=("맑은 고딕", 14, "bold"),
            fg=self.colors["white"],
            bg=self.colors["header"]
        ).pack()
        
        Label(
            header_frame,
            text=f"혈액형: {patient.blood_type} | {status_icon} {status_text}",
            font=("맑은 고딕", 10),
            fg=self.colors["light"],
            bg=self.colors["header"]
        ).pack()
        
        info_frame = Frame(dialog, bg=self.colors["white"])
        info_frame.pack(fill=BOTH, expand=True, padx=20, pady=15)
        
        sections = [
            ("📅 입원 정보", [
                ("입원일", patient.date_of_admission),
                ("퇴원일", patient.discharge_date if patient.discharge_date else "-"),
                ("입원유형", patient.get_admission_type_korean()),
                ("병실", f"{patient.room_number}호" if patient.room_number else "-")
            ]),
            ("🩺 의료 정보", [
                ("진단명", f"{patient.get_condition_korean()} ({patient.medical_condition})"),
                ("담당의", patient.doctor),
                ("병원", patient.hospital),
                ("처방약", patient.medication if patient.medication else "-"),
                ("검사결과", patient.get_test_results_korean())
            ]),
            ("💰 비용 정보", [
                ("보험사", patient.insurance_provider if patient.insurance_provider else "-"),
                ("청구금액", patient.get_billing_formatted())
            ])
        ]
        
        for section_title, items in sections:
            Label(
                info_frame, text=section_title,
                font=("맑은 고딕", 11, "bold"),
                bg=self.colors["white"],
                fg=self.colors["dark"]
            ).pack(anchor=W, pady=(10, 5))
            
            for label, value in items:
                row_frame = Frame(info_frame, bg=self.colors["light"])
                row_frame.pack(fill=X, pady=2)
                Label(
                    row_frame, text=f"  {label}:",
                    font=("맑은 고딕", 10),
                    bg=self.colors["light"],
                    width=12, anchor=E
                ).pack(side=LEFT)
                Label(
                    row_frame, text=f"  {value}",
                    font=("맑은 고딕", 10),
                    bg=self.colors["light"],
                    anchor=W
                ).pack(side=LEFT, fill=X, expand=True)
        
        Button(
            dialog, text="닫기", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=dialog.destroy
        ).pack(pady=15, ipadx=20)
    
    def delete_selected(self):
        """선택된 환자 삭제"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "삭제할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", f"환자 정보를 찾을 수 없습니다. (ID: {patient_id})")
            return
        
        confirm = messagebox.askyesno(
            "삭제 확인",
            f"정말 삭제하시겠습니까?\n\n환자: {patient.name} ({patient_id})"
        )
        
        if confirm:
            success, msg = self.manager.delete(patient_id)
            if success:
                messagebox.showinfo("삭제 완료", msg)
                self.refresh_table()
            else:
                messagebox.showerror("삭제 실패", msg)
    
    def discharge_patient(self):
        """환자 퇴원 처리"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "퇴원 처리할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", f"환자 정보를 찾을 수 없습니다. (ID: {patient_id})")
            return
        
        if not patient.is_hospitalized():
            messagebox.showinfo("알림", f"{patient.name} 환자는 이미 퇴원했습니다.")
            return
        
        confirm = messagebox.askyesno(
            "퇴원 확인",
            f"{patient.name} 환자를 퇴원 처리하시겠습니까?"
        )
        
        if confirm:
            success, msg = self.manager.discharge_patient(patient_id)
            if success:
                messagebox.showinfo("퇴원 완료", f"{patient.name} 환자가 퇴원 처리되었습니다.")
                self.refresh_table()
            else:
                messagebox.showerror("퇴원 처리 실패", msg)
    
    def show_statistics(self):
        """통계 보기"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        stats = self.manager.get_statistics()
        
        if not stats:
            messagebox.showinfo("통계 없음", "환자 데이터가 없습니다.")
            return
        
        dialog = Toplevel(self)
        dialog.title("📊 환자 통계")
        dialog.geometry("500x520")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self)
        
        Label(
            dialog, text="📊 환자 통계 현황",
            font=("맑은 고딕", 14, "bold"),
            bg=self.colors["white"]
        ).pack(pady=15)
        
        stats_frame = Frame(dialog, bg=self.colors["white"])
        stats_frame.pack(fill=BOTH, expand=True, padx=20)
        
        # 기본 통계
        Label(
            stats_frame, text="─── 기본 통계 ───",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["white"]
        ).pack(anchor=W, pady=(10, 5))
        
        basic_stats = [
            ("총 환자 수", f"{stats['total_patients']}명"),
            ("남성", f"{stats['male_count']}명 ({stats['male_ratio']}%)"),
            ("여성", f"{stats['female_count']}명 ({stats['female_ratio']}%)"),
            ("평균 나이", f"{stats['avg_age']}세"),
            ("입원 중", f"{stats['hospitalized_count']}명"),
            ("퇴원", f"{stats['discharged_count']}명"),
        ]
        
        for label, value in basic_stats:
            row = Frame(stats_frame, bg=self.colors["light"])
            row.pack(fill=X, pady=2)
            Label(
                row, text=label, font=("맑은 고딕", 10),
                bg=self.colors["light"], width=15, anchor=E
            ).pack(side=LEFT)
            Label(
                row, text=value, font=("맑은 고딕", 10, "bold"),
                bg=self.colors["light"], fg=self.colors["header"]
            ).pack(side=LEFT, padx=10)
        
        # 진단명별 분포
        Label(
            stats_frame, text="─── 진단명별 분포 ───",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["white"]
        ).pack(anchor=W, pady=(15, 5))
        
        for condition, count in sorted(stats['conditions'].items(), key=lambda x: x[1], reverse=True):
            row = Frame(stats_frame, bg=self.colors["light"])
            row.pack(fill=X, pady=2)
            Label(
                row, text=condition, font=("맑은 고딕", 10),
                bg=self.colors["light"], width=15, anchor=E
            ).pack(side=LEFT)
            Label(
                row, text=f"{count}명", font=("맑은 고딕", 10, "bold"),
                bg=self.colors["light"], fg=self.colors["dark"]
            ).pack(side=LEFT, padx=10)
        
        # 비용 통계
        Label(
            stats_frame, text="─── 비용 통계 ───",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["white"]
        ).pack(anchor=W, pady=(15, 5))
        
        billing_stats = [
            ("평균 청구금액", f"₩{stats['avg_billing']:,.0f}"),
            ("총 청구금액", f"₩{stats['total_billing']:,.0f}"),
        ]
        
        for label, value in billing_stats:
            row = Frame(stats_frame, bg=self.colors["light"])
            row.pack(fill=X, pady=2)
            Label(
                row, text=label, font=("맑은 고딕", 10),
                bg=self.colors["light"], width=15, anchor=E
            ).pack(side=LEFT)
            Label(
                row, text=value, font=("맑은 고딕", 10, "bold"),
                bg=self.colors["light"], fg=self.colors["success"]
            ).pack(side=LEFT, padx=10)
        
        Button(
            dialog, text="닫기", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=dialog.destroy
        ).pack(pady=15, ipadx=20)
    
    def _init_integration(self, base_path):
        """건강 체크 시스템 연동 초기화"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from integration import IntegrationManager
            self.integration_manager = IntegrationManager(base_path)
        except Exception as e:
            print(f"[PatientManagementApp] 연동 초기화 오류: {e}")
            self.integration_manager = None
    
    def show_health_records(self):
        """선택된 환자의 건강 기록 조회"""
        if not self.manager:
            messagebox.showerror("오류", "데이터 매니저가 초기화되지 않았습니다.")
            return
        
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            messagebox.showwarning("선택 필요", "건강 기록을 조회할 환자를 선택하세요.")
            return
        
        patient = self.manager.read_by_id(patient_id)
        if not patient:
            messagebox.showerror("오류", f"환자 정보를 찾을 수 없습니다. (ID: {patient_id})")
            return
        
        # 연동 매니저 확인
        if not self.integration_manager:
            messagebox.showinfo("알림", "건강 체크 시스템과 연동되지 않았습니다.")
            return
        
        # 환자 ID로 건강 기록 조회
        records = self.integration_manager.get_health_records_by_patient(patient_id)
        
        # ID로 못 찾으면 이름으로 검색
        if not records:
            records = self.integration_manager.get_health_records_by_name(patient.name)
        
        # 건강 기록 다이얼로그
        dialog = Toplevel(self)
        dialog.title(f"💓 건강 기록 - {patient.name} ({patient_id})")
        dialog.geometry("700x450")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["white"])
        dialog.transient(self)
        
        # 헤더
        header = Frame(dialog, bg="#27ae60", pady=10)
        header.pack(fill=X)
        
        Label(
            header,
            text=f"💓 {patient.name}님의 건강 기록 히스토리",
            font=("맑은 고딕", 12, "bold"),
            fg="white",
            bg="#27ae60"
        ).pack()
        
        Label(
            header,
            text=f"환자 ID: {patient_id} | 나이: {patient.age}세 | 진단명: {patient.get_condition_korean()}",
            font=("맑은 고딕", 9),
            fg="#ecf0f1",
            bg="#27ae60"
        ).pack()
        
        # 기록 테이블
        if records:
            table_frame = Frame(dialog, bg=self.colors["white"])
            table_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
            
            columns = ("date", "bmi", "bp", "risk", "status")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
            
            tree.heading("date", text="날짜")
            tree.heading("bmi", text="BMI")
            tree.heading("bp", text="혈압")
            tree.heading("risk", text="위험도")
            tree.heading("status", text="상태")
            
            tree.column("date", width=130)
            tree.column("bmi", width=80)
            tree.column("bp", width=100)
            tree.column("risk", width=80)
            tree.column("status", width=100)
            
            for r in records:
                bmi = float(r.get("bmi", 0))
                risk = int(r.get("risk_score", 0))
                
                # 상태 판정
                if risk >= 60:
                    status = "🔴 위험"
                elif risk >= 40:
                    status = "⚠️ 주의"
                else:
                    status = "🟢 양호"
                
                tree.insert("", END, values=(
                    r.get("date", ""),
                    f"{bmi:.1f}",
                    f"{r.get('ap_hi', '')}/{r.get('ap_lo', '')}",
                    f"{risk}점",
                    status
                ))
            
            scrollbar = Scrollbar(table_frame, orient=VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # 추이 분석
            trend = self.integration_manager.get_health_trend(patient_id)
            if trend:
                trend_frame = Frame(dialog, bg=self.colors["light"], relief=RIDGE, bd=1)
                trend_frame.pack(fill=X, padx=20, pady=5)
                
                Label(
                    trend_frame,
                    text=f"📈 추이 분석 (총 {trend['record_count']}건)",
                    font=("맑은 고딕", 10, "bold"),
                    bg=self.colors["light"]
                ).pack(side=LEFT, padx=10, pady=8)
                
                Label(
                    trend_frame,
                    text=f"BMI: {trend['bmi_trend']} | 혈압: {trend['bp_trend']} | 위험도: {trend['risk_trend']}",
                    font=("맑은 고딕", 10),
                    bg=self.colors["light"]
                ).pack(side=LEFT, padx=10, pady=8)
        else:
            Label(
                dialog,
                text="📭 저장된 건강 기록이 없습니다.",
                font=("맑은 고딕", 12),
                bg=self.colors["white"],
                fg="#666"
            ).pack(expand=True)
            
            Label(
                dialog,
                text="건강 상태 체크 시스템에서 이 환자를 선택하여\n건강 체크를 진행하면 기록이 연동됩니다.",
                font=("맑은 고딕", 10),
                bg=self.colors["white"],
                fg="#999"
            ).pack()
        
        Button(
            dialog, text="닫기", font=("맑은 고딕", 10),
            bg=self.colors["light"], fg=self.colors["dark"],
            relief=FLAT, command=dialog.destroy
        ).pack(pady=15, ipadx=20)
    
    def start_health_check(self):
        """선택된 환자로 건강 체크 시작"""
        patient_id = self.get_selected_patient_id()
        patient = None
        
        if patient_id:
            patient = self.manager.read_by_id(patient_id)
        
        # 건강 체크 시스템 열기
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from health_app.health_gui import HealthCheckApp
            
            # base_path 가져오기
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            health_app = HealthCheckApp(self, base_path)
            
            # 선택된 환자가 있으면 정보 자동 입력
            if patient:
                health_app.name_entry.delete(0, END)
                health_app.name_entry.insert(0, patient.name)
                
                health_app.age_entry.delete(0, END)
                health_app.age_entry.insert(0, str(patient.age))
                
                health_app.gender_var.set("남성" if patient.gender == "Male" else "여성")
                
                # 환자 선택 콤보박스가 있으면 설정
                if hasattr(health_app, 'patient_combo_var') and hasattr(health_app, 'selected_patient_id'):
                    health_app.selected_patient_id = patient_id
                    # 콤보박스에서 해당 환자 찾아서 선택
                    for i, p in enumerate(health_app.patient_list):
                        if p[0] == patient_id:
                            combo_text = f"{p[0]} - {p[1]} ({p[2]}세, {'남' if p[3]=='Male' else '여'})"
                            health_app.patient_combo_var.set(combo_text)
                            break
                
                messagebox.showinfo("건강 체크", f"{patient.name} 환자의 건강 체크를 시작합니다.\n기본 정보가 자동으로 입력되었습니다.")
            else:
                messagebox.showinfo("건강 체크", "건강 상태 체크 시스템을 시작합니다.\n환자를 선택하거나 신규로 입력하세요.")
                
        except Exception as e:
            messagebox.showerror("오류", f"건강 체크 시스템을 열 수 없습니다.\n{str(e)}")
