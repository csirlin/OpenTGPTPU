#define VERTICES 5
#define EDGES 10

/*
      0
     /
    1
   / \
  2---3
       \
        4
*/

int nodes[VERTICES + 1] = {0, 1, 4, 6, 9, 10};
int edges[EDGES] = {1, 0, 2, 3, 1, 3, 1, 2, 4, 3};
int length[VERTICES] = {0, -1 , -1, -1, -1};
int to_visit[VERTICES];
int to_visit_end = 0;
int to_visit_start = 0;

int add_to_visit(int val) {
    to_visit[to_visit_end++] = val;
    return 0;
}

int get_top() {
    return to_visit[to_visit_start++];
}

int search(int start, int goal) {
    add_to_visit(start);

    while (to_visit_start != to_visit_end) {
        int proc_node = get_top();
        int proc_len = length[proc_node];
        int first = nodes[proc_node];
        int last = nodes[proc_node + 1];
        for (int i = first; i < last; i++) {
            int e = edges[i];
            if (e < VERTICES) {
                int len = length[e];
                int curr_len = proc_len + 1;
                if (len == -1) {
                    length[e] = curr_len;
                    add_to_visit(e);
                }
                if (curr_len < len) {
                    length[e] = curr_len;
                }
            }

        }
    }
    return length[goal];
}


int gpmm_main(void) {
    return search(0, 3);
}