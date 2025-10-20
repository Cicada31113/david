- from __future__ import annoatations

"미래 주석 해석 방식"을 켜서 타입 표기를 더 자유롭게 쓰게함.
파이썬이 소스 코드를 읽을 때 타입힌트를 문자열처럼 다뤄서 (순환참조, 선언순서) 문제를 피함.

*순환참조*
두 모듈이나 클래스가 서로를 동시에 참조할 때 생기는 문제.

'''python
# a.py
from b import B
class A: ...

# b.py
from a import A
class B: ...
'''
a를 불러오면 b를 불러오고,