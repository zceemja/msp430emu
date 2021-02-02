/*
 Compatibility functions for windows msvc compiler
*/
#ifndef _WIN_H_
#define _WIN_H_

#ifdef _MSC_VER

#define strncasecmp(x,y,z) _strnicmp(x,y,z)
void usleep(__int64 usec);

#endif

#endif