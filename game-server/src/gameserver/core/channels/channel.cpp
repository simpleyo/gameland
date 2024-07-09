// Copyright 2014, Alex Horn. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

#include "core/channels/channel.h"

namespace cpp
{
}

// EJEMPLO:
//
//#include <iostream>
//#include "core/channels/channel.h"
//
//void thread_a(cpp::channel<char> c) {
//    for (;;) 
//    {
//        char r = c.recv();
//        std::cout << r << std::endl;
//    }
//}
//
//void thread_b(cpp::channel<char> c) {
//    for (;;) 
//    {
//        c.send('B');
//    }
//}
//
//void thread_c(cpp::channel<char> c) {
//    for (;;) 
//    {
//        c.send('C');
//    }
//}
//
//int main() {
//    cpp::channel<char> ch;
//
//    std::thread a(thread_a, ch);
//    std::thread b(thread_b, ch);
//    std::thread c(thread_c, ch);
//
//    a.join();
//    b.join();
//    c.join();
//
//    return EXIT_SUCCESS;
//}