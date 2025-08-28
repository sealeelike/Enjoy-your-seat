from manim import *

class FullDemo(Scene):
    def construct(self):
        # ===================== 参数配置区 =====================
        self.camera.background_color = WHITE
        ROWS = 20
        COLS = 8
        GRID_WIDTH, GRID_HEIGHT = 10, 6
        STROKE_WIDTH = 2

        L1_GRID = 3      # 竖线
        L1_HLINE = 1     # 横线
        L2_FILL = 2      # 色块
        L3_OVER = 4     # 其它顶层内容

        FONT_CELL = 19
        FONT_LABEL = 20
        FONT_ANNOTATION = 28
        COLOR_TEXT = BLACK

        COLOR_AVAILABLE = GREEN
        COLOR_UNAVAILABLE = GREY
        COLOR_ABANDON = GREY
        COLOR_FLASH = RED

        left, right = -GRID_WIDTH/2, GRID_WIDTH/2
        bottom, top = -GRID_HEIGHT/2, GRID_HEIGHT/2

        unavailable_ranges = [
            "B6:B8","C6:C19","D4:D19","E4:E8","E12:E18","F6:F7","F12:F18","G2","G8:G11","H2:H20"
        ]
        available_ranges = [
            "B2:B5","B9:B20",
            "C2:C5","C20",
            "D2:D3","D20",
            "E2:E3","E9:E11","E19:E20",
            "F2:F5","F8:F11","F19:F20",
            "G3:G7","G12:G20"
        ]

        # ===================== 共享基础区 =====================
        outer = Rectangle(width=GRID_WIDTH, height=GRID_HEIGHT,
                          stroke_color=BLACK, stroke_width=STROKE_WIDTH)
        vertical_lines = VGroup(*[
            Line([left + i*GRID_WIDTH/COLS, bottom, 0],
                 [left + i*GRID_WIDTH/COLS, top, 0],
                 stroke_color=BLACK, stroke_width=STROKE_WIDTH)
            for i in range(1, COLS)
        ])
        horizontal_lines = VGroup(*[
            Line([left, bottom + i*GRID_HEIGHT/ROWS, 0],
                 [right, bottom + i*GRID_HEIGHT/ROWS, 0],
                 stroke_color=BLACK, stroke_width=STROKE_WIDTH)
            for i in range(1, ROWS)
        ])
        outer.set_z_index(L1_GRID)
        vertical_lines.set_z_index(L1_GRID)
        horizontal_lines.set_z_index(L1_HLINE)
        self.add(outer, vertical_lines, horizontal_lines)

        def cell_center(row:int, col:int):
            cw, ch = GRID_WIDTH/COLS, GRID_HEIGHT/ROWS
            x = left + (col-0.5)*cw
            y = top - (row-0.5)*ch
            return [x, y, 0]

        def parse_cell(cell:str):
            col_letter = cell[0].upper()
            row = int(cell[1:])
            col = ord(col_letter) - ord('A') + 1
            return row, col

        def norm_range(rng:str):
            if ":" not in rng:
                r, c = parse_cell(rng)
                return f"{chr(ord('A')+c-1)}{r}:{chr(ord('A')+c-1)}{r}"
            a, b = [s.strip() for s in rng.split(":")]
            r1, c1 = parse_cell(a); r2, c2 = parse_cell(b)
            rl, rh = min(r1, r2), max(r1, r2)
            cl, ch = min(c1, c2), max(c1, c2)
            return f"{chr(ord('A')+cl-1)}{rl}:{chr(ord('A')+ch-1)}{rh}"

        def y_edges_of_range(range_str:str):
            s = norm_range(range_str)
            start, end = s.split(":")
            r1, _ = parse_cell(start)
            r2, _ = parse_cell(end)
            ch = GRID_HEIGHT/ROWS
            y_top_edge = top - (r1-1)*ch
            y_bottom_edge = top - (r2)*ch
            return y_top_edge, y_bottom_edge

        def col_center_x(col):
            if isinstance(col, str):
                col = ord(col.upper()) - ord('A') + 1
            cw = GRID_WIDTH/COLS
            return left + (col-0.5)*cw

        def put_text(row:int, col:int, content:str, font_size:int=FONT_CELL, color=COLOR_TEXT):
            t = Text(content, font_size=font_size, color=color)
            cw, ch = GRID_WIDTH/COLS, GRID_HEIGHT/ROWS
            max_w, max_h = cw*0.9, ch*0.9
            if t.width > max_w: t.scale_to_fit_width(max_w)
            if t.height > max_h: t.scale_to_fit_height(max_h)
            t.move_to(cell_center(row, col))
            t.set_z_index(L3_OVER)
            self.add(t)
            return t

        def put(cell:str, content:str, font_size:int=FONT_CELL, color=COLOR_TEXT):
            r, c = parse_cell(cell)
            return put_text(r, c, content, font_size, color)

        put("A1", "Time")
        for idx, col_letter in enumerate("BCDEFGH", start=1):
            put(f"{col_letter}1", f"FB{idx:03d}")
        for i in range(19):  # A2..A20
            total_min = 8*60 + 30*i
            hh, mm = divmod(total_min, 60)
            put(f"A{2+i}", f"{hh:02d}:{mm:02d}")

        # 添加色块和标签，仅供 abandon 用
        range_to_rect = {}
        range_to_label = {}
        def rect_for_range(range_str:str, fill_color=YELLOW, opacity:float=1.0, margin:float=-0.01):
            s = norm_range(range_str)
            start, end = s.split(":")
            r1, c1 = parse_cell(start)
            r2, c2 = parse_cell(end)
            cw, ch = GRID_WIDTH/COLS, GRID_HEIGHT/ROWS
            x1 = left + (c1-1)*cw + margin
            x2 = left + (c2)*cw - margin
            y1 = top - (r2)*ch + margin
            y2 = top - (r1-1)*ch - margin
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            rect = Rectangle(width=w, height=h, fill_color=fill_color,
                             fill_opacity=opacity, stroke_width=0)
            rect.move_to([(x1+x2)/2, (y1+y2)/2, 0])
            rect.set_z_index(L2_FILL)
            return rect

        def label_on(rect:Rectangle, text:str, color=COLOR_TEXT, font_size:int=FONT_LABEL):
            t = Text(text, color=color, font_size=font_size)
            max_w, max_h = rect.width*0.9, rect.height*0.9
            if t.width > max_w: t.scale_to_fit_width(max_w)
            if t.height > max_h: t.scale_to_fit_height(max_h)
            t.move_to(rect.get_center())
            t.set_z_index(L3_OVER)
            self.add(t)
            return t

        for rng in unavailable_ranges:
            s = norm_range(rng)
            r = rect_for_range(s, fill_color=COLOR_UNAVAILABLE, opacity=1.0)
            self.add(r)
            lbl = label_on(r, "unavailable", COLOR_TEXT, FONT_LABEL)
            range_to_rect[s] = r
            range_to_label[s] = lbl
        for rng in available_ranges:
            s = norm_range(rng)
            r = rect_for_range(s, fill_color=COLOR_AVAILABLE, opacity=1.0)
            self.add(r)
            lbl = label_on(r, "available", COLOR_TEXT, FONT_LABEL)
            range_to_rect[s] = r
            range_to_label[s] = lbl

        # 注释（出现->停留->消失）
        def show_annotation(msg: str,
                            appear: float = 0.35,
                            hold: float = 0.8,
                            disappear: float = 0.3,
                            y_gap: float = 0.6,
                            start_delay: float = 0.0):
            y = outer.get_bottom()[1] - y_gap
            t = Text(msg, font_size=FONT_ANNOTATION, color=COLOR_TEXT)
            max_w = GRID_WIDTH * 0.95
            if t.width > max_w: t.scale_to_fit_width(max_w)
            t.move_to([0, y, 0])
            t.set_z_index(L3_OVER)
            t.set_opacity(0)
            self.add(t)

            total = start_delay + appear + hold + disappear
            elapsed = 0.0

            def upd(m, dt):
                nonlocal elapsed
                elapsed += dt
                if elapsed < start_delay:
                    m.set_opacity(0)
                    return
                t1 = elapsed - start_delay
                if t1 < appear:
                    m.set_opacity(t1 / max(1e-6, appear))
                elif t1 < appear + hold:
                    m.set_opacity(1.0)
                elif t1 < appear + hold + disappear:
                    t2 = t1 - appear - hold
                    m.set_opacity(max(0.0, 1.0 - t2 / max(1e-6, disappear)))
                else:
                    m.set_opacity(0.0)
                    m.remove_updater(upd)
                    self.remove(m)

            t.add_updater(upd)
            # 返回对象可选，不必用
            return t


        # ===================== 新增函数区 =====================
        # 1. 指定范围block边缘闪烁
        def flash_block_outline(range_str: str,
                                period: float = 0.6,
                                flashes: int = 3,
                                color = COLOR_FLASH,
                                stroke_width: float = 6,
                                margin: float = 0.0,
                                start_delay: float = 0.0):
            s = norm_range(range_str)
            start, end = s.split(":")
            r1, c1 = parse_cell(start)
            r2, c2 = parse_cell(end)
            cw, ch = GRID_WIDTH/COLS, GRID_HEIGHT/ROWS
            x1 = left + (c1-1)*cw + margin
            x2 = left + (c2)*cw - margin
            y1 = top - (r2)*ch + margin
            y2 = top - (r1-1)*ch - margin
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            outline = Rectangle(width=w, height=h, fill_opacity=0,
                                stroke_color=color, stroke_width=stroke_width)
            outline.move_to([(x1+x2)/2, (y1+y2)/2, 0])
            outline.set_z_index(L3_OVER)
            outline.set_stroke(opacity=0.0)
            self.add(outline)

            elapsed = 0.0
            total = start_delay + period * flashes

            def upd(m, dt):
                nonlocal elapsed
                elapsed += dt
                if elapsed < start_delay:
                    m.set_stroke(opacity=0.0)
                    return
                t1 = elapsed - start_delay
                if t1 >= period * flashes:
                    m.set_stroke(opacity=0.0)
                    m.remove_updater(upd)
                    self.remove(m)
                    return
                # 一个周期内：前半亮，后半暗（简单粗暴）
                in_cycle = t1 % period
                on = 1.0 if in_cycle < (period * 0.5) else 0.0
                m.set_stroke(opacity=on)

            outline.add_updater(upd)
            return outline


        # 2. 横向贯穿线闪烁
        def flash_hline_for_range(
                range_or_list,
                which: str = 'top',
                period: float = 0.6,
                flashes: int = 3,
                color = RED,
                stroke_width: float = 6,
                left_extra: float = 0.0,
                right_extra: float = 0.0,
                start_delay: float = 0.0,
                keep_after: bool = False,  # 新增: 是否保留
                hold_after: float = 1.0    # 新增: 保留多久，0为不额外保留
            ):
            ranges = range_or_list if isinstance(range_or_list, (list, tuple)) else [range_or_list]
            lines = []
            elapsed = 0.0

            def make_updater(line):
                nonlocal elapsed
                total_flash = start_delay + period * flashes

                def upd(m, dt):
                    nonlocal elapsed
                    elapsed += dt
                    if elapsed < start_delay:
                        m.set_stroke(opacity=0.0)
                        return
                    t1 = elapsed - start_delay
                    if t1 >= period*flashes:
                        if not keep_after:
                            m.set_stroke(opacity=0.0)
                            m.remove_updater(upd)
                            self.remove(m)
                        else:
                            m.set_stroke(opacity=1.0)
                            m.remove_updater(upd)
                            # 保留线条，后续处理
                        return
                    in_cycle = t1 % period
                    on = 1.0 if in_cycle < (period * 0.5) else 0.0
                    m.set_stroke(opacity=on)
                return upd

            for rng in ranges:
                y_top, y_bottom = y_edges_of_range(rng)
                y = y_top if which == 'top' else y_bottom
                line = Line(
                    start=[left - left_extra, y, 0],
                    end=[right + right_extra, y, 0],
                    stroke_color=color,
                    stroke_width=stroke_width
                )
                line.set_z_index(L3_OVER)
                line.set_stroke(opacity=0.0)
                self.add(line)
                line.add_updater(make_updater(line))
                lines.append(line)

            # 保留后自动消失功能：直接在主Scene里安排
            if keep_after:
                # 总时间 = 闪烁时间 + 保留时间
                total_time = start_delay + period * flashes + hold_after
                def later_remove(lines=lines):
                    for l in lines:
                        self.play(FadeOut(l), run_time=0.3)
                # 延迟任务：你用 self.wait(total_time)，然后调用
                self.wait(start_delay + period*flashes)
                if hold_after > 0:
                    self.wait(hold_after)
                    for l in lines:
                        self.play(FadeOut(l), run_time=0.3)
            return lines


        # 3. 将 available block 变灰，并添加 abandon 标签
        def abandon_range(range_str: str, recolor_time: float = 0.3):
            s = norm_range(range_str)
            rect = range_to_rect.get(s)
            if rect is None:
                return
            self.play(rect.animate.set_fill(COLOR_ABANDON, 1.0), run_time=recolor_time)
            old_lbl = range_to_label.get(s)
            if old_lbl:
                self.play(FadeOut(old_lbl), run_time=0.2)
            new_lbl = label_on(rect, "abandon", COLOR_TEXT, FONT_LABEL)
            range_to_label[s] = new_lbl

        # 4. 批量闪烁
        def flash_many_blocks(ranges, period=0.6, flashes=3,
                              color=COLOR_FLASH, stroke_width=6):
            for rng in ranges:
                flash_block_outline(rng, period=period, flashes=flashes,
                                    color=color, stroke_width=stroke_width)

        # 5. 批量 abandon
        def abandon_many(ranges, recolor_time: float = 0.25):
            for rng in ranges:
                abandon_range(rng, recolor_time=recolor_time)

        # 6. 表格右侧纵向时间轴闪烁，并保持
        def flash_vline_right(range_str: str,
                              period: float = 0.6,
                              flashes: int = 3,
                              color = RED,
                              stroke_width: float = 6,
                              x_gap: float = 0.8):
            y_top, y_bottom = y_edges_of_range(range_str)
            x = right + x_gap
            vline = Line([x, y_top, 0], [x, y_bottom, 0],
                         stroke_color=color, stroke_width=stroke_width)
            vline.set_z_index(L3_OVER)
            for i in range(flashes):
                self.play(FadeIn(vline), run_time=period/2)
                if i < flashes - 1:
                    self.play(FadeOut(vline), run_time=period/2)
            self.add(vline)
            return vline

        # 7. 移动时间轴到指定列中心
        def move_timeline_to_col_center(vline: VMobject, col, run_time: float = 0.6):
            x = col_center_x(col)
            target = vline.copy().move_to([x, vline.get_center()[1], 0])
            self.play(Transform(vline, target), run_time=run_time)
            return vline

        # 8. 移动时间轴到表格最右侧
        def move_timeline_to_right_side(vline: VMobject, x_gap: float = 0.9, run_time: float = 0.6):
            x = right + x_gap
            target = vline.copy().move_to([x, vline.get_center()[1], 0])
            self.play(Transform(vline, target), run_time=run_time)
            return vline

        # 9. 复制并把指定 block 平移到目标 x（最通用）
        def slide_range_to_x(range_str: str,
                            x_target: float,
                            copy: bool = True,
                            align: str = 'center',   # 'center' | 'left' | 'right'，相对矩形对齐点
                            gap: float = 0.0,        # 当 align 为 'left'/'right' 时的额外间隙
                            run_time: float = 0.6,
                            with_label: bool = True):
            s = norm_range(range_str)
            rect = range_to_rect.get(s)
            if rect is None:
                return None

            lbl = range_to_label.get(s) if with_label else None

            # 复制还是移动原件
            if copy:
                rect2 = rect.copy()
                self.add(rect2)
                if lbl:
                    lbl2 = lbl.copy()
                    self.add(lbl2)
                    grp = VGroup(rect2, lbl2)
                else:
                    grp = VGroup(rect2)
            else:
                grp = VGroup(rect) if lbl is None else VGroup(rect, lbl)

            # 放到最上层，避免被网格遮住
            grp.set_z_index(L2_FILL)

            # 计算水平位移（只动 x，不改 y）
            if align == 'center':
                dx = x_target - rect.get_center()[0]
            elif align == 'left':
                dx = (x_target + gap) - rect.get_left()[0]
            elif align == 'right':
                dx = (x_target - gap) - rect.get_right()[0]
            else:
                dx = x_target - rect.get_center()[0]  # 兜底 center

            self.play(grp.animate.shift(RIGHT * dx), run_time=run_time)
            return grp


        # 10. 把指定 block 平移到时间轴 vline（更省心的封装）
        def slide_range_to_vline(range_str: str,
                                vline: VMobject,
                                copy: bool = True,
                                align: str = 'center',  # 'center' | 'left' | 'right'
                                gap: float = 0.0,
                                run_time: float = 0.6,
                                with_label: bool = True):
            x_target = vline.get_center()[0]
            return slide_range_to_x(range_str, x_target,
                                    copy=copy, align=align, gap=gap,
                                    run_time=run_time, with_label=with_label)


        # 11. 批量把多个 block 平移到同一个时间轴（顺序依次播放）
        def slide_many_to_vline(ranges: list,
                                vline: VMobject,
                                copy: bool = True,
                                align: str = 'center',
                                gap: float = 0.0,
                                run_time: float = 0.6,
                                lag: float = 0.1,
                                with_label: bool = True):
            moved = []
            for rng in ranges:
                g = slide_range_to_vline(rng, vline,
                                        copy=copy, align=align, gap=gap,
                                        run_time=run_time, with_label=with_label)
                moved.append(g)
                if lag > 0:
                    self.wait(lag)
            return moved


        # ===================== 函数调用区 =====================
        
        self.wait(1)

        show_annotation("First, the app gets the timetable for the day.", hold=2.0)
        self.wait(3)
     
        show_annotation("The app will pre-process the data.", hold=2.0)
        self.wait(3)

        show_annotation("It will first remove smaller time blocks,", hold=3.0)
        flash_block_outline("D2:D3", period=1, flashes=4, color=RED, stroke_width=6)
        self.wait(3.5)
        
        flash_hline_for_range(["D2","D4"], which='top', period=1, flashes=5, color=YELLOW, stroke_width=6,left_extra=-1.3, right_extra=-2.5)
        self.wait(2)
        flash_many_blocks(["B2:B5","C2:C5","F2:F5"], period=0.6, flashes=4, color=RED, stroke_width=6)
        show_annotation("those that are completely contained in other available time blocks." , hold=5.0)
        self.wait(7)

        flash_block_outline("D2:D3", period=0.5, flashes=3, color=RED, stroke_width=6)
        show_annotation("We abandon it.", hold=2.0)
        self.wait(3)
        abandon_range("D2:D3", recolor_time=0.3)

        
        show_annotation("so do other small blocks", hold=1.5)
        self.wait(3)
        flash_many_blocks(["C20","D20","E2:E3","E9:E11","E19:E20","F19:F20","G12:G20"], period=0.45, flashes=5, color=ORANGE, stroke_width=6)
        self.wait(4)
        abandon_many(["C20","D20","E2:E3","E9:E11","E19:E20","F19:F20","G12:G20"], recolor_time=0.25)
        self.wait(3)


        show_annotation("Now, data preprocessing is finished.", hold=2.0)
        self.wait(3.2)
        show_annotation("The app reads user needs and provides solutions.", hold=2.5)
        self.wait(3.2)

        show_annotation("Let's say that the user needs to use the room from 8:30-17:00.", hold=3.0)
        self.wait(1.3)
        
        vline = flash_vline_right("B3:B19", period=0.6, flashes=4, color=BLUE, stroke_width=8, x_gap=0.9)
        self.wait(2)
        
        
        show_annotation("The app tries to find a single available block that covers the entire day.", hold=5.0)
        self.wait(3)
        flash_many_blocks(["B2:B5","B9:B20","C2:C5","F2:F5","F8:F11","G3:G7"], period=1, flashes=7, color=RED, stroke_width=6)
        self.wait(3)
        move_timeline_to_col_center(vline, "G", run_time=1)
        move_timeline_to_col_center(vline, "F", run_time=1)
        move_timeline_to_col_center(vline, "C", run_time=1)
        move_timeline_to_col_center(vline, "B", run_time=1)

        self.wait(1)
        show_annotation("However, no single block can satisfy the requirement.", hold=5.0)
        move_timeline_to_col_center(vline, "I", run_time=0.5)

        self.wait(5.5)
        

        show_annotation("The app will consider combination solutions.", hold=2.3)
        self.wait(3)
        show_annotation("It looks for blocks that cover the start and end times.", hold=2.5)
        self.wait(1)
        
        flash_hline_for_range(["B3","B20"], which='top', period=1, flashes=3, color=YELLOW, stroke_width=5,left_extra=-1.2, right_extra=1,keep_after=True, hold_after=1)

        flash_many_blocks(["B2:B5","B9:B20","C2:C5","F2:F5","G3:G7"], period=0.8, flashes=4, color=RED, stroke_width=5)
        self.wait(3)
        
        show_annotation("For each time block candidate, ", hold=3)
        self.wait(4)
        show_annotation("it selects the one whose boundary is farthest from the included endpoint,", hold=6)
        self.wait(4)
        
        flash_many_blocks(["G3:G7","B9:B20"], period=0.8, flashes=6, color=ORANGE, stroke_width=5)
        self.wait(3)
        show_annotation("and verify whether they meet the requirements", hold=4)
        self.wait(4)
        
        flash_many_blocks(["G3:G7","B9:B20"], period=1, flashes=4, color=RED, stroke_width=5)
        slide_range_to_vline("G3:G7", vline, copy=True, align='left', gap=-0.3, run_time=1.3)
        self.wait(1)
        slide_range_to_vline("B9:B20", vline, copy=True, align='left', gap=-0.3, run_time=1.3)
        self.wait(1)
        
        
        show_annotation("If not, it continues to look for blocks covering the gap.", hold=6)
        self.wait(2)
        flash_hline_for_range(["F8","F9"], which='top', period=1, flashes=3, color=YELLOW, stroke_width=5,left_extra=-1.2, right_extra=1,keep_after=True, hold_after=0.3)
        self.wait(1)

        flash_block_outline("F8:F11", period=0.5, flashes=3, color=RED, stroke_width=5)
        self.wait(1)
        slide_range_to_vline("F8:F11", vline, copy=True, align='left', gap=-0.3, run_time=1.3)
        self.wait(2)
        
        show_annotation("finally, it finds a combination that covers the entire duration.", hold=5)
        self.wait(0.5)
        flash_many_blocks(["G3:G7","F8:F11","B9:B20"], period=1, flashes=4, color=RED, stroke_width=5)    
        self.wait(5)

        
