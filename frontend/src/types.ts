export type Product = { id:number; category:number; category_name:string; name:string; slug:string; description:string; image_url:string; price:string; stock:number; is_active:boolean }
export type CartItem = { id:number; product:number; quantity:number; line_total:string; product_detail:Product }
export type Order = { id:number; total:string; subtotal:string; status:string; shipping_address:string; payment_status:string; created_at:string; items:{id:number;product_name:string;unit_price:string;quantity:number;line_total:string}[] }
