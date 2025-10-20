# git checkout -b new
 
#  new라는 새로운 브랜치를 생성하며 

# git reset --soft HEAD^

#  현재 브랜치를 직전 커밋으로 되돌리되, 되돌린 커밋의 변경사항은 스테이징 상태로

# git merge --abort
# 병합 취소 병합시작전 상태로 되돌림


# git featch
# 원격 저장소 최신 변경사항을 로컬로 가져오되, 현재 작업브랜치에는 병합x

# git branch -u origin/new feature
# 현재 체크아웃된 로컬브랜치의 upstream

#git commit --amend -m
# 가장 최근 커밋 수정