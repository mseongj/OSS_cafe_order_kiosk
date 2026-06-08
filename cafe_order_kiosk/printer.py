from escpos.printer import Dummy
from cafe_order_kiosk.models import Order
from cafe_order_kiosk.utils import format_money

class ReceiptPrinter:
    def __init__(self, use_hardware: bool = False):
        self.use_hardware = use_hardware
        try:
            if self.use_hardware:
                # 실제 USB 프린터가 연결되었을 때 (Vendor ID, Product ID는 기기마다 다름)
                from escpos.printer import Usb
                self.p = Usb(0x04b8, 0x0202, 0, out_ep=0x01) 
            else:
                self.p = Dummy()
        except Exception as e:
            print(f"[프린터 연결 실패] 가상 모드로 전환합니다: {e}")
            self.p = Dummy()

    def print_receipt(self, order: Order):
        """Order 객체를 받아 영수증을 포맷팅하고 출력 명령을 전송합니다."""
        p = self.p

        p.set(align='center', bold=True, width=2, height=2)
        p.text("CAFE KIOSK\n")
        p.set(align='center', bold=False, width=1, height=1)
        p.text("--------------------------------\n")
        
        p.set(align='left')
        p.text(f"주문 번호 : #{order.id}\n")
        if order.paid_at:
            p.text(f"결제 일시 : {order.paid_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        p.text("--------------------------------\n")
        
        # 3. 메뉴 리스트
        for item in order.items:
            name_str = f"{item.name} x{item.quantity}"
            price_str = format_money(item.line_total)
            
            spaces = 32 - len(name_str) - len(price_str)
            if spaces < 1: spaces = 1
            
            p.text(f"{name_str}{' ' * spaces}{price_str}\n")
            if item.options:
                p.text(f"  └ 옵션: {', '.join(item.options)}\n")

        p.text("--------------------------------\n")
        
        p.set(align='right', bold=True)
        p.text(f"총 결제 금액: {format_money(order.total)} 원\n\n")
        
        p.set(align='center', bold=False)
        if order.payment:
            p.text(f"결제 수단: {order.payment.method}\n")
        
        p.barcode(str(order.id).zfill(6), 'CODE39', 64, 2, '', '')
        p.text("\n이용해 주셔서 감사합니다.\n\n")
        
        p.cut()

        if isinstance(self.p, Dummy):
            print("\n[가상 프린터 렌더링 완료 - 실제 하드웨어 연결 시 영수증이 출력됩니다]")
            print(self.p.output)