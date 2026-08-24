from __future__ import annotations

import asyncio
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any
import customtkinter as ctk

# ---------------------------------------------------------------------------
# Project root bootstrap
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Project Tools Registry Adapter
# ---------------------------------------------------------------------------
class ConsoleToolClient:
    def __init__(self, tools: dict[str, Any]):
        self._tools = tools

    async def get_tools(self) -> list[Any]:
        return list(self._tools.values())

def build_project_tool_registry() -> dict[str, Any]:
    from tools.booking_tools import get_nearby_airports, get_flight_options, get_bookings_by_flight
    from tools.customer_tools import get_customer_profile, get_booking_history, UpdateCustomerProfile
    from tools.finance_and_decision_tools import (
        CalculateTripCost, CheckRefundEligibility, CalculateRefundAmount,
        ProcessRefund, CalculateCompensation, IssueTravelVoucher, CompareRebookingCost
    )
    from tools.travel_status_tools import (
        get_flight_status, get_delay_duration, check_disruption_reason,
        get_weather, check_airport_status, check_connection_risk,
        get_estimated_departure, get_estimated_arrival, check_alternative_transport, get_disruption_severity
    )
    from tools.escalation_tools import (
        escalate_to_human, create_support_ticket, schedule_agent_callback,
        notify_supervisor, log_escalation
    )

    project_tools = [
        get_nearby_airports, get_flight_options, get_bookings_by_flight,
        get_customer_profile, get_booking_history, UpdateCustomerProfile,
        CalculateTripCost, CheckRefundEligibility, CalculateRefundAmount,
        ProcessRefund, CalculateCompensation, IssueTravelVoucher, CompareRebookingCost,
        get_flight_status, get_delay_duration, check_disruption_reason,
        get_weather, check_airport_status, check_connection_risk,
        get_estimated_departure, get_estimated_arrival, check_alternative_transport, get_disruption_severity,
        escalate_to_human, create_support_ticket, schedule_agent_callback, notify_supervisor, log_escalation
    ]
    return {tool.name: tool for tool in project_tools}

_LOCAL_CLIENT: ConsoleToolClient | None = None

def get_local_client() -> ConsoleToolClient:
    global _LOCAL_CLIENT
    if _LOCAL_CLIENT is None:
        _LOCAL_CLIENT = ConsoleToolClient(build_project_tool_registry())
    return _LOCAL_CLIENT


# ---------------------------------------------------------------------------
# GUI Application Main Class
# ---------------------------------------------------------------------------
class WanderPathGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WanderPath Travel AI Assistant")
        self.geometry("1100x700")
        
        # System Appearance
        ctk.set_appearance_mode("Light")
        
        # Color Palette Definition
        self.COLOR_BG = "#F4F7FA"             
        self.COLOR_SIDEBAR = "#0A192F"        
        self.COLOR_SIDEBAR_BTN = "#172A45"    
        self.COLOR_ACCENT = "#0056B3"         
        self.COLOR_ACCENT_HOVER = "#003D82"   
        self.COLOR_USER_BUBBLE = "#0066FF"     
        self.COLOR_AGENT_BUBBLE = "#E6F0FA"    
        self.COLOR_TEXT_MAIN = "#1E293B"      

        self.configure(fg_color=self.COLOR_BG)

        # State & Async Execution Tracking Variables
        self.current_agent_key = "1"
        self.user_id = "C001"
        self.loop = asyncio.new_event_loop()
        
        # Task Cancellation Controls
        self.current_task_id = 0
        self.current_async_task: asyncio.Task | None = None

        # Loading Animation Controls
        self.loading_frame = None
        self.loading_label = None
        self.loading_dots_count = 0
        self.loading_after_id = None

        # Start Async Loop background thread
        threading.Thread(target=self._start_async_loop, daemon=True).start()

        # Build UI Layout
        self._build_sidebar()
        self._build_chat_area()

        # Welcome message
        self.append_message("System", "Welcome to WanderPath Travel AI System! Select an agent from the sidebar and start chatting.", is_user=False)

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    # ---------------------------------------------------------------------------
    # UI Layout Construction
    # ---------------------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=self.COLOR_SIDEBAR)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Title / Brand Label
        title_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="WANDERPATH", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(padx=20, pady=(25, 5))

        subtitle_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Travel Agent Suite", 
            font=ctk.CTkFont(size=12),
            text_color="#8892B0"
        )
        subtitle_label.pack(padx=20, pady=(0, 25))

        # Agent Select Buttons
        self.agent_buttons = {}
        agents = [
            ("1", "Memory & RAG Agent"),
            ("2", "Flight Agent"),
            ("3", "Planning Agent"),
            ("4", "Refund Agent"),
            ("5", "VIP Agent")
        ]

        for key, name in agents:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=name,
                anchor="w",
                height=45,
                corner_radius=8,
                fg_color=self.COLOR_ACCENT if key == self.current_agent_key else self.COLOR_SIDEBAR_BTN,
                hover_color=self.COLOR_ACCENT_HOVER,
                text_color="#FFFFFF",
                font=ctk.CTkFont(size=14, weight="normal"),
                command=lambda k=key: self.select_agent(k)
            )
            btn.pack(fill="x", padx=15, pady=6)
            self.agent_buttons[key] = btn

    def _build_chat_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        # Top Bar: Agent Indicator
        self.top_bar = ctk.CTkFrame(self.main_frame, height=50, fg_color="#FFFFFF", corner_radius=10)
        self.top_bar.pack(fill="x", pady=(0, 10))
        self.top_bar.pack_propagate(False)

        self.agent_status_label = ctk.CTkLabel(
            self.top_bar,
            text="Active Agent: Memory & RAG Agent",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.COLOR_TEXT_MAIN
        )
        self.agent_status_label.pack(side="left", padx=20, pady=10)

        # Scrollable Chat Box
        self.chat_scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="#FFFFFF", corner_radius=10)
        self.chat_scroll.pack(fill="both", expand=True, pady=(0, 10))

        # Bottom Input Area
        self.input_frame = ctk.CTkFrame(self.main_frame, height=60, fg_color="transparent")
        self.input_frame.pack(fill="x")

        self.entry_message = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type your message here...",
            height=48,
            corner_radius=24,
            border_color="#CBD5E1",
            fg_color="#FFFFFF",
            text_color=self.COLOR_TEXT_MAIN,
            font=ctk.CTkFont(size=14)
        )
        self.entry_message.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_message.bind("<Return>", lambda event: self.send_message())

        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=90,
            height=48,
            corner_radius=24,
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.send_message
        )
        self.btn_send.pack(side="right")

    # ---------------------------------------------------------------------------
    # Business Logic & Interaction
    # ---------------------------------------------------------------------------
    def clear_chat(self):
        """مسح جميع عناصر الشات الحالية وإيقاف مؤشر التحميل"""
        self.hide_loading_indicator()
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()

    def select_agent(self, key: str):
        """إلغاء التنسيق القديم ومسح الشات والتحويل إلى الـ Agent الجديد فورا"""
        if self.current_agent_key == key:
            return

        # 1. إلغاء أي Task async شغال في الخلفية للـ Agent القديم
        self.current_task_id += 1
        if self.current_async_task and not self.current_async_task.done():
            self.loop.call_soon_threadsafe(self.current_async_task.cancel)

        # 2. تغيير Agent المحدد في الواجهة
        self.current_agent_key = key
        for k, btn in self.agent_buttons.items():
            if k == key:
                btn.configure(fg_color=self.COLOR_ACCENT)
                self.agent_status_label.configure(text=f"Active Agent: {btn.cget('text')}")
            else:
                btn.configure(fg_color=self.COLOR_SIDEBAR_BTN)

        # 3. تصفير الشات وإضافة رسالة ترحيب خاصة بالـ Agent الجديد
        self.clear_chat()
        self.append_message("System", f"Switched to {self.agent_buttons[key].cget('text')}. Previous session cleared.", is_user=False)

    def append_message(self, sender: str, text: str, is_user: bool = False):
        bubble_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=5, padx=10)

        align = "e" if is_user else "w"
        bg_color = self.COLOR_USER_BUBBLE if is_user else self.COLOR_AGENT_BUBBLE
        text_color = "#FFFFFF" if is_user else self.COLOR_TEXT_MAIN

        msg_box = ctk.CTkFrame(bubble_frame, fg_color=bg_color, corner_radius=14)
        msg_box.pack(side="right" if is_user else "left", anchor=align, padx=5)

        lbl_sender = ctk.CTkLabel(
            msg_box,
            text=sender,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#E2E8F0" if is_user else "#475569"
        )
        lbl_sender.pack(anchor="w", padx=12, pady=(8, 2))

        lbl_text = ctk.CTkLabel(
            msg_box,
            text=text,
            font=ctk.CTkFont(size=13),
            text_color=text_color,
            wraplength=600,
            justify="left"
        )
        lbl_text.pack(anchor="w", padx=12, pady=(0, 8))

        # Auto scroll to bottom
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    # ---------------------------------------------------------------------------
    # Loading Animation Functions (3 Dots Typing Indicator)
    # ---------------------------------------------------------------------------
    def show_loading_indicator(self):
        """إظهار فقرة تحتوي على 3 نقاط متحركة للتحميل"""
        self.hide_loading_indicator()

        self.loading_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self.loading_frame.pack(fill="x", pady=5, padx=10)

        msg_box = ctk.CTkFrame(self.loading_frame, fg_color=self.COLOR_AGENT_BUBBLE, corner_radius=14)
        msg_box.pack(side="left", anchor="w", padx=5)

        lbl_sender = ctk.CTkLabel(
            msg_box,
            text=self.agent_buttons[self.current_agent_key].cget("text"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        )
        lbl_sender.pack(anchor="w", padx=12, pady=(8, 2))

        self.loading_label = ctk.CTkLabel(
            msg_box,
            text=".",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLOR_TEXT_MAIN
        )
        self.loading_label.pack(anchor="w", padx=12, pady=(0, 8))

        self.loading_dots_count = 1
        self._animate_loading_dots()
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def _animate_loading_dots(self):
        """التحكم بالحركة الدورية للنقاط الثلاث"""
        if self.loading_label and self.loading_label.winfo_exists():
            self.loading_dots_count = (self.loading_dots_count % 3) + 1
            dots_text = ". " * self.loading_dots_count
            self.loading_label.configure(text=dots_text.strip())
            self.loading_after_id = self.after(400, self._animate_loading_dots)

    def hide_loading_indicator(self):
        """إخفاء فقرة التحميل وإيقاف الـ Timer"""
        if self.loading_after_id:
            self.after_cancel(self.loading_after_id)
            self.loading_after_id = None

        if self.loading_frame and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()

        self.loading_frame = None
        self.loading_label = None

    # ---------------------------------------------------------------------------
    # Send & Task Dispatcher
    # ---------------------------------------------------------------------------
    def send_message(self):
        user_text = self.entry_message.get().strip()
        if not user_text:
            return

        self.entry_message.delete(0, "end")
        self.append_message("You", user_text, is_user=True)

        # إظهار نقاط التحميل فور الإرسال
        self.show_loading_indicator()

        # تجهيز Task جُديد مع حفظ معرف العملية لمنع التداخل عند السويتش
        self.current_task_id += 1
        task_id = self.current_task_id

        self.current_async_task = asyncio.run_coroutine_threadsafe(
            self.process_agent_request(task_id, self.current_agent_key, user_text),
            self.loop
        )

    # ---------------------------------------------------------------------------
    # Agent Executors Router
    # ---------------------------------------------------------------------------
    async def process_agent_request(self, task_id: int, agent_key: str, user_input: str):
        try:
            if agent_key == "1":
                await self.exec_memory_rag(task_id, user_input)
            elif agent_key == "2":
                await self.exec_flight(task_id, user_input)
            elif agent_key == "3":
                await self.exec_planning(task_id, user_input)
            elif agent_key == "4":
                await self.exec_refund(task_id, user_input)
            elif agent_key == "5":
                await self.exec_vip(task_id, user_input)
        except asyncio.CancelledError:
            pass # تم تحويل الـ Agent وإلغاء المهمة بنجاح
        except Exception as exc:
            if task_id == self.current_task_id:
                self.after(0, self._handle_agent_response, task_id, "Error", f"Execution error: {exc}")

    def _handle_agent_response(self, task_id: int, sender: str, text: str):
        """طباعة نتيجة الـ Agent في الشات إذا لم يقم المستخدم بتغيير الـ Agent في هذه الأثناء"""
        if task_id == self.current_task_id:
            self.hide_loading_indicator()
            self.append_message(sender, text, is_user=False)

    # 1. Memory & RAG Agent
    async def exec_memory_rag(self, task_id: int, prompt: str):
        from agent.agent import run_agent
        result = await run_agent(client=get_local_client(), user_input=prompt, user_id=self.user_id)
        self.after(0, self._handle_agent_response, task_id, "Memory & RAG Agent", str(result))

    # 2. Flight Agent
    async def exec_flight(self, task_id: int, prompt: str):
        from state_graph.graphs.flight_rebooking import start_run
        run_id = f"flight-gui-{int(time.time())}"
        initial_state = {
            "flight_id": 2,
            "customer_id": 5,
            "customer_is_vip": False,
            "user_prompt": prompt,
            "customer_response": None,
            "connected_services": None,
            "rebooking_plan": None,
            "alternatives_tried": [],
            "proposed_alternative": None,
            "airline_response": None,
            "refund_amount": None,
            "refund_decision": None,
            "refund_approved": None,
            "final_outcome": None,
        }
        result = start_run(run_id, initial_state)
        self.after(0, self._handle_agent_response, task_id, "Flight Agent", str(result))

    # 3. Planning Agent
    async def exec_planning(self, task_id: int, prompt: str):
        from planning import planning_agent as planning_module
        from planning.environment import TravelEnvironment

        class ConsoleTravelEnvironment(TravelEnvironment):
            def __init__(self, mcp_client=None, **kwargs):
                super().__init__(mcp_tools={})
                self.mcp_tools = getattr(mcp_client, "_tools", {}) if mcp_client else {}

        orig_env = planning_module.TravelEnvironment
        planning_module.TravelEnvironment = ConsoleTravelEnvironment

        try:
            result = await planning_module.run_planning_agent(
                client=get_local_client(),
                goal=prompt,
                mode="decomposition_first",
            )
            self.after(0, self._handle_agent_response, task_id, "Planning Agent", str(result))
        finally:
            planning_module.TravelEnvironment = orig_env

    # 4. Refund Agent
    async def exec_refund(self, task_id: int, prompt: str):
        from state_graph.refundGraph.refund_graph import start_run
        run_id = f"refund-gui-{int(time.time())}"
        result = await start_run(
            run_id=run_id,
            initial_state={"booking_id": 101, "employee_id": 5, "prompt": prompt},
            tools=get_local_client()._tools,
        )
        self.after(0, self._handle_agent_response, task_id, "Refund Agent", str(result))

    # 5. VIP Agent
    async def exec_vip(self, task_id: int, prompt: str):
        from state_graph.graphs.vip_trip_customization import vip_trip_graph
        thread_id = f"vip-gui-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}
        result = vip_trip_graph.invoke({"customer_id": self.user_id, "prompt": prompt}, config)
        self.after(0, self._handle_agent_response, task_id, "VIP Agent", str(result))


# ---------------------------------------------------------------------------
# App Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = WanderPathGUI()
    app.mainloop()