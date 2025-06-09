fn program_1_5__2() -> i32 {
    return ;
    }

fn program_1_5__3() {
    return 1;
    }

fn program_2_1__2() {
    let mut b;
    }

fn program_2_1__3() {
    let mut a:i32;
    let mut a;
    let mut a:i32;
    }

fn program_2_2__2() {
    a=32;
    }

fn program_2_3__2() {
    let mut b:i32=a;
    }

fn program_2_3__3() {
    let mut a:i32;
    let mut b:i32=a;
    }

fn program_3_3__3__a() {
    }

fn program_3_3__3__b() {
    program_3_3__3__a(1);
    }

fn program_3_3__4__a(mut a:i32) {
    }

fn program_3_3__4__b() {
    program_3_3__4__a(program_3_3__4__a);
    }

fn program_3_3__5__a() {
    }

fn program_3_3__5__b() {
    let mut a=program_3_3__5__a();
    }

fn program_5_4__2() {
    break;
    }

fn program_5_4__4() {
    continue;
    }

fn program_6_1__2() {
    let c:i32=1;
    c=2;
    }

fn program_6_2__3() {
    let mut a:i32=1;
    let mut b=*a;
    }

fn program_6_2__4() {
    let mut a:i32=1;
    let b=&a;
    let mut c=&mut a;
    }

fn program_6_2__5() {
    let a:i32=1;
    let mut b=&mut a;
    }

fn program_7_4__2() {
    break 2;
    }

fn program_8_1__2(mut a:i32) {
    let mut a:[i32;2];
    a=1;
    }

fn program_8_1__3(mut a:i32) {
    let mut a:[i32;2];
    a=[1,2,3];
    }

fn program_8_1__4() {
    let mut a=[[i32;1];1];
    a=[1];
    }

fn program_8_2__2(mut a:i32) {
    let mut a=[1,2,3];
    let mut b=a[a];
    }

fn program_8_2__3() {
    let mut a=[1,2,3];
    let mut b=a[3];
    }

fn program_8_2__4() {
    let a:[i32;3]=[1,2,3];
    a[0]=4;
    }

fn program_9_1__2(mut a:i32) {
    let mut a:(i32,i32);
    a=1;
    }

fn program_9_1__3(mut a:i32) {
    let mut a:(i32,i32);
    a=(1,2,3);
    }

fn program_9_1__4() {
    let mut a=((i32,i32),);
    a=(1,);
    }

fn program_9_2__2(mut a:i32) {
    let mut a=(1,2,3);
    let mut b=a.a;
    }

fn program_9_2__3() {
    let mut a=(1,2,3);
    let mut b=a.3;
    }

fn program_9_2__4() {
    let a:(i32,i32,i32)=(1,2,3);
    a.0=4;
    }