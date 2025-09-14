# Install script for directory: /home/sky/github/stable-retro/third-party/capnproto/c++/src/kj

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "RelWithDebInfo")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/libkj.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj" TYPE FILE FILES
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/common.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/units.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/memory.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/refcount.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/array.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/vector.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/string.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/string-tree.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/exception.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/debug.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/arena.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/miniposix.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/io.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/tuple.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/one-of.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/function.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/mutex.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/thread.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/threadlocal.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/main.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/windows-sanity.h"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj/parse" TYPE FILE FILES
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/parse/common.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/parse/char.h"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj/std" TYPE FILE FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/std/iostream.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/libkj-test.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj" TYPE FILE FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/test.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj/compat" TYPE FILE FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/compat/gtest.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/libkj-async.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj" TYPE FILE FILES
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/async-prelude.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/async.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/async-inl.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/async-unix.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/async-win32.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/async-io.h"
    "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/time.h"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/libkj-http.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/kj/compat" TYPE FILE FILES "/home/sky/github/stable-retro/third-party/capnproto/c++/src/kj/compat/http.h")
endif()

