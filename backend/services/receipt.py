import os
from datetime import datetime
from fpdf import FPDF

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansSC-Regular.ttf")


class ReceiptPDF(FPDF):
    def __init__(self):
        super().__init__()
        if os.path.exists(FONT_PATH):
            self.add_font(fname=FONT_PATH)
            self._font_name = "NotoSansSC"
        else:
            self._font_name = "Helvetica"

    def set_cn_font(self, size=10):
        self.set_font(self._font_name, size=size)


class ReceiptService:
    @staticmethod
    def generate_order_receipt(
        order_no: str,
        member_name: str,
        subject: str,
        amount: float,
        discount: float,
        actual_amount: float,
        payment_method: str,
        payment_status: str,
        paid_at: str | None = None,
        org_name: str = "FitAI",
        org_address: str = "",
        org_phone: str = "",
    ) -> bytes:
        pdf = ReceiptPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # Header
        pdf.set_cn_font(20)
        pdf.cell(w=0, text=org_name, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_cn_font(14)
        pdf.cell(w=0, text="收  据", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_draw_color(100, 100, 100)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)

        # Receipt info
        pdf.set_cn_font(10)
        pdf.cell(w=0, text=f"收据编号: {order_no}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=0, text=f"开具日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Customer info
        pdf.cell(w=0, text=f"客户姓名: {member_name}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=0, text=f"购买项目: {subject}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Amount table
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(3)
        pdf.set_cn_font(10)
        pdf.cell(w=80, text="项目", align="C", border=1)
        pdf.cell(w=40, text="金额", align="C", border=1)
        pdf.cell(w=70, text="备注", align="C", border=1)
        pdf.ln()

        pdf.cell(w=80, text=subject, border=1)
        pdf.cell(w=40, text=f"¥{amount:.2f}", align="R", border=1)
        pdf.cell(w=70, text="原价", border=1)
        pdf.ln()

        if discount > 0:
            pdf.cell(w=80, text="优惠减免", border=1)
            pdf.cell(w=40, text=f"-¥{discount:.2f}", align="R", border=1)
            pdf.cell(w=70, text="", border=1)
            pdf.ln()

        pdf.set_cn_font(12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(w=80, text="实付金额", border=1, fill=True)
        pdf.cell(w=40, text=f"¥{actual_amount:.2f}", align="R", border=1, fill=True)
        pdf.cell(w=70, text="", border=1, fill=True)
        pdf.ln()
        pdf.ln(5)

        # Payment info
        pdf.set_cn_font(10)
        method_map = {
            "wechat": "微信支付", "alipay": "支付宝",
            "cash": "现金", "transfer": "银行转账",
        }
        pdf.cell(w=0, text=f"支付方式: {method_map.get(payment_method, payment_method)}", new_x="LMARGIN", new_y="NEXT")
        status_map = {"paid": "已支付", "pending": "待支付", "refunded": "已退款", "cancelled": "已取消"}
        pdf.cell(w=0, text=f"支付状态: {status_map.get(payment_status, payment_status)}", new_x="LMARGIN", new_y="NEXT")
        if paid_at:
            pdf.cell(w=0, text=f"支付时间: {paid_at}", new_x="LMARGIN", new_y="NEXT")

        # Footer
        pdf.ln(10)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)
        pdf.set_cn_font(8)
        if org_address:
            pdf.cell(w=0, text=f"地址: {org_address}", new_x="LMARGIN", new_y="NEXT")
        if org_phone:
            pdf.cell(w=0, text=f"电话: {org_phone}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(w=0, text="此收据由 FitAI 系统自动生成", align="C", new_x="LMARGIN", new_y="NEXT")

        return bytes(pdf.output())
