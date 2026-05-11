[1mdiff --git a/.github/workflows/sync_to_hf_yml b/.github/workflows/sync_to_hf_yml[m
[1mnew file mode 100644[m
[1mindex 0000000..61eb009[m
[1m--- /dev/null[m
[1m+++ b/.github/workflows/sync_to_hf_yml[m
[36m@@ -0,0 +1,19 @@[m
[32m+[m[32mname: Sync to Hugging Face hub[m
[32m+[m[32mon:[m
[32m+[m[32m  push:[m
[32m+[m[32m    branches: [main][m
[32m+[m[32m  force_push:[m
[32m+[m[32m    branches: [main][m
[32m+[m
[32m+[m[32mjobs:[m
[32m+[m[32m  sync-to-hub:[m
[32m+[m[32m    runs-on: ubuntu-latest[m
[32m+[m[32m    steps:[m
[32m+[m[32m      - uses: actions/checkout@v3[m
[32m+[m[32m        with:[m
[32m+[m[32m          fetch-depth: 0[m
[32m+[m[32m          lfs: true[m
[32m+[m[32m      - name: Push to hub[m
[32m+[m[32m        env:[m
[32m+[m[32m          HF_TOKEN: ${{ secrets.HF_TOKEN }}[m
[32m+[m[32m        run: git push --force https://YellowAlberto:$HF_TOKEN@huggingface.co/spaces/YellowAlberto/ReciclA main[m
\ No newline at end of file[m
