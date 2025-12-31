#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <iostream>

namespace py = pybind11;

void hello() {
	std::cout << "hi" << std::endl;
}

PYBIND11_MODULE(playback, m) {
    m.def("hello", &hello, "says hi lol");
}
