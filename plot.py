@@
 def plot_degree(t=3, r_p=10, alpha=5, matrices=None, save=None):
@@
-    fig, ax = plt.subplots(figsize=(9, 5))
-
-    # Define distinct markers and linestyles for clarity
-    markers = ['o', 's', '^', 'd', 'v', 'P', '*']
-    linestyles = ['-', '--', ':', '-.', '-', '--']
-
-    plotted = 0
-    for idx, name in enumerate(matrices):
-        history = data.get(name)
-        if not history:
-            continue
-        rounds = [h[0] for h in history]
-        maxdeg = [h[2] for h in history]
-        color = COLORS.get(name, None)
-        label = LABELS.get(name, name)
-        m = markers[idx % len(markers)]
-        ls = linestyles[idx % len(linestyles)]
-        # plot line and markers; use slightly transparent lines so overlaps show
-        ax.plot(rounds, maxdeg, marker=m, linestyle=ls, linewidth=2, markersize=6,
-                color=color, label=label, alpha=0.9, zorder=10-idx)
-        plotted += 1
-
-    if plotted == 0:
-        ax.text(0.5, 0.5, 'No degree data to plot', ha='center', va='center')
-
-    ax.set_xlabel('Round', fontsize=12)
-    ax.set_ylabel('Max algebraic degree (upper bound)', fontsize=12)
-    ax.set_title(f'Algebraic degree growth over partial rounds  |  t={t}, α={alpha}', fontsize=13)
-    ax.set_xticks(range(r_p + 1))
-    ax.legend(fontsize=10)
-    ax.grid(True, alpha=0.3)
-
-    fig.tight_layout()
-    if save:
-        fig.savefig(save, dpi=150)
-        print(f"Saved: {save}")
-    else:
-        plt.show()
+    # Group identical max-degree histories to avoid overplotting
+    series_map = {}
+    for name in matrices:
+        hist = data.get(name)
+        if not hist:
+            continue
+        key = tuple(h[2] for h in hist)
+        series_map.setdefault(key, []).append(name)
+
+    fig, ax = plt.subplots(figsize=(9, 5))
+    markers = ['o', 's', '^', 'd', 'v', 'P', '*']
+    linestyles = ['-', '--', ':', '-.']
+
+    for i, (series, names_group) in enumerate(series_map.items()):
+        rounds = list(range(len(series)))
+        maxdeg = list(series)
+        label = ", ".join(LABELS.get(n, n) for n in names_group)
+        color = COLORS.get(names_group[0], None)
+        m = markers[i % len(markers)]
+        ls = linestyles[i % len(linestyles)]
+        ax.plot(rounds, maxdeg, marker=m, linestyle=ls, linewidth=2, markersize=6,
+                color=color, label=label, alpha=0.95)
+
+    ax.set_xlabel('Round', fontsize=12)
+    ax.set_ylabel('Max algebraic degree (upper bound)', fontsize=12)
+    ax.set_title(f'Algebraic degree growth over partial rounds  |  t={t}, α={alpha}', fontsize=13)
+    ax.set_xticks(range(r_p + 1))
+    ax.legend(fontsize=9)
+    ax.grid(True, alpha=0.3)
+
+    fig.tight_layout()
+    if save:
+        fig.savefig(save, dpi=150)
+        print(f"Saved: {save}")
+    else:
+        plt.show()
