fn program_1_1() {
 }

fn program_1_2() {
    ;;;;;;
}

fn program_1_3(){
    return ;
    }

fn program_1_4(mut a:i32) {
    }

fn program_1_5__1() -> i32 {
    return 1;
    }

fn program_2_1__1() {
    let mut a:i32;
    }

fn program_2_2__1(mut a:i32) {
    a=32;
    }

fn program_2_3__1() {
    let mut a:i32=1;
    let mut b=1;
    }

fn program_2_3__4() {
    let mut a:i32=1;
    let mut a=2;
    let mut a:i32=3;
    }

fn program_3_1__1() {
    0;
    (1);
    ((2));
    (((3)));
    }

fn program_3_1__2(mut a:i32) {
    a;
    (a);
    ((a));
    (((a)));
    }

fn program_3_2() {
    1*2/3;
    4+5/6;
    7<8;
    9>10;
    11==12;
    13!=14;
    1*2+3*4!=4/2-3/1;
    }

fn program_3_3__1__a() {
    }

fn program_3_3__1__b() {
    program_3_3__1__a();
    }

fn program_3_3__2__a(mut a:i32) {
    }

fn program_3_3__2__b() {
    program_3_3__2__a(1+2);
    }

fn program_4_1__1(mut a:i32) -> i32
{
    if a>0 {
        return 1;
    }
}

fn program_4_1__2(mut a:i32) -> i32
{
    if a>0 {
        return 1;
    }
    else {
        return 0;
    }
}

fn program_4_2(mut a:i32) -> i32 {
    if a>0 {
        return a+1;
    }
    else if a<0 {
        return a-1;
    }
    else {
        return 0;
    }
}

fn program_5_1(mut n:i32) {
    while n>0 {
        n=n-1;
        }
    }

fn program_5_2(mut n:i32) {
    for mut i in 1..n+1 {
        n=n-1;
        }
    }

fn program_5_3() {
    loop {
        }
    }

fn program_5_4__1() {
    while 1==1 {
        break;
        }
    }

fn program_5_4__3() {
    while 1==0 {
        continue;
        }
    }

fn program_6_1__1() {
    let a:i32=1;
    let b=2;
    }

fn program_6_2__1() {
    let mut a:i32=1;
    let mut b:&mut i32=&mut a;
    let mut c:i32=*b;
    }

fn program_6_2__2() {
    let a:i32=1;
    let b:& i32=&a;
    let c:i32=*b;
    }

fn program_6_2__6() {
    let mut a:i32=1;
    let b=&a;
    let c=&a;
    }

fn program_7_1(mut x:i32,mut y:i32) {
    let mut z={
        let mut t=x*x+x;
        t=t+x*y;
        t
        };
    }

fn program_7_2(mut x:i32,mut y:i32) -> i32 {
    let mut t=x*x+x;
    t=t+x*y;
    t
    }

fn program_7_3(mut a:i32) {
    let mut b=if a>0 {
        1
        } else {
        0
        };
    }

fn program_7_4__1() {
    let mut a=loop {
        break 1;
        };
    }