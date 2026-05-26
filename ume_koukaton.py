import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 550  # ゲームウィンドウの幅
HEIGHT = 700  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，卵などのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Life(pg.sprite.Sprite):
    """
    残機数に関するクラス
    """
    def __init__(self, num: int):
        super().__init__()
        points = [(16*math.sin(t/100)**3 +20,
                   -(13*math.cos(t/100)-5*math.cos(2*t/100)-2*math.cos(3*t/100)-math.cos(3*t/100)-math.cos(4*t/100)) +20
                   ) for t in range(0,628) ]
        self.li_img = pg.Surface((40, 40))
        self.li_img.set_colorkey((0, 0, 0))
        pg.draw.polygon(self.li_img, (255, 0, 0), points)
        self.num = num
        

    def update(self, screen: pg.Surface):
        for i in range(self.num):
            rect = self.li_img.get_rect()
            rect.center = WIDTH-50 - i*50, HEIGHT-50
            screen.blit(self.li_img, rect)
            


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
        self.image = self.imgs[self.dire]  # 通常画像のセット

        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    風に関するクラス
    """
    def __init__(self, emy: "Enemy", bird: Bird):
        """
        引数1 emy：爆弾を投下する雑魚敵
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 風の半径：10以上50以下の乱数
        img = pg.image.load("fig/wind.png")
        self.image = pg.transform.scale(img, (2*rad, 2*rad))
        self.rect = self.image.get_rect()
        # 風を飛ばすemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Egg(pg.sprite.Sprite):
    """
    卵に関するクラス
    """
    def __init__(self, bird: Bird):
        """
        卵画像Surfaceを生成する
        引数 egg：卵を放つこうかとん
        """
        super().__init__()
        self.vx = 0
        self.vy = -1  
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/egg.png"), 0, 0.2)
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        卵を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    雑魚敵に関するクラス
    """
    imgs = [pg.image.load(f"fig/bird{i}.png") for i in range(1, 5)]
    
    def __init__(self, bird: Bird):
        super().__init__()
        self.type = random.randint(0,3)
        bird_image = __class__.imgs[self.type]
        self.image = pg.transform.scale(bird_image, (50,50))
        self.rect = self.image.get_rect()
        self.damage = 0
        
        if (self.type == 0) or (self.type == 1):
            self.rect.center = random.randint(0, WIDTH), 0
            self.vx, self.vy = 0, +6
            self.bound = random.randint(50, HEIGHT//2)  # 停止位置
            self.state = "down"  # 降下状態or停止状態
            self.interval = random.randint(50, 300)  # 爆弾投下インターバル
            self.hp = 3
        elif (self.type == 2) or (self.type == 3):
            self.rect.center = random.randint(25, WIDTH-25), 30
            self.state = "run"
            self.speed = 15                              
            self.vx, self.vy = calc_orientation(self.rect, bird.rect)
            self.vx = self.vx * self.speed
            self.vy = self.vy * self.speed
            self.hp = 1

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if (self.type == 0) or (self.type == 1):
            if self.rect.centery > self.bound:
                self.vy = 0
                self.state = "stop"
            self.rect.move_ip(self.vx, self.vy)
        else:
            self.rect.move_ip(self.vx, self.vy)
            if check_bound(self.rect) != (True, True):
                self.kill()

        bird_image = __class__.imgs[self.type]
        self.image = pg.transform.scale(bird_image, (50, 50))
        if self.damage > 0:
            red = pg.Surface((50, 50))
            pg.draw.rect(red, (255, 0, 0), (0, 0, 50, 50))
            red.set_alpha(180)
            self.image.blit(red, (0, 0))
            self.damage -= 1
        

class Boss(pg.sprite.Sprite):
    """
    ボスに関するクラス
    """
    imgs = [pg.image.load(f"fig/karasu.jpeg")]
    
    def __init__(self, num: int):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2, 0
        self.vx, self.vy = 0, +2
        self.bound = 140  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.life = num
        self.interval = 10  # 羽投下インターバル

    def update(self):
        """
        ボスを速度ベクトルself.vyに基づき移動（降下）させる
        停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Wing(pg.sprite.Sprite):
    """
    羽に関するクラス
    """
    img = pg.image.load(f"fig/wing.jpeg")

    def __init__(self):
        """
        羽Surfaceを生成する
        """
        super().__init__()
        self.image = pg.transform.rotozoom(self.img, 180, 0.2)
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.centerx = random.randint(0, WIDTH)
        self.rect.centery = 75
        self.speed = 8

    def update(self):
        """
        羽を速度 self.speedに基づき下に移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(0, self.speed)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Boss_HP:
    """
    ボスHPに関するクラス
    """

    def __init__(self, max_life):
        self.max_life = max_life
        self.color = (255, 0, 0)

    def draw(self, screen, life):
        width = WIDTH / self.max_life

        for i in range(life):
            rect = pg.Rect(i * width, 0, width, 30)
            pg.draw.rect(screen, self.color, rect)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Item(pg.sprite.Sprite):
    """
    獲得すると特殊な効果を発揮するアイテムに関するクラス
    """
    def __init__(self, emy_rect: pg.Rect):
        """
        倒された敵の位置にアイテムを生成する
        """
        super().__init__()
        # アイテムの種類をランダムで決定
        self.kind = random.choice(["Score", "Speed", "Life"])
        self.font = pg.font.Font(None, 30)
        
        # 種類に応じたテキストの色を設定
        if self.kind == "Score":
            color = (255, 215, 0)   # 金色（スコアアップ）
        elif self.kind == "Speed":
            color = (0, 255, 0)     # 緑色（移動速度アップ）
        else:
            color = (255, 105, 180) # ピンク（残機回復）
            
        self.image = self.font.render(self.kind, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = emy_rect.center
        self.vy = +3
    
    def update(self):
        """
        アイテムを落下させ、画面外に出たら削除する
        """
        self.rect.move_ip(0, self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    life = Life(3)
    boss_value = 1
    boss_life = 20

    bird = Bird(3, (WIDTH/2, HEIGHT-200))
    bombs = pg.sprite.Group()
    eggs = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    items = pg.sprite.Group()  # アイテムグループを追加
    boss = pg.sprite.Group()
    wings = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                eggs.add(Egg(bird))
        screen.blit(bg_img, [0, 0])

        if score.value >= 100:
            if boss_value >= 1:
                if len(boss) == 0:
                    boss.add(Boss(boss_life))
                    boss_HP = Boss_HP(boss_life)
                    boss_value -= 1
        else:
            if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
                emys.add(Enemy(bird))
               
        for bos in boss:
            boss_HP.draw(screen, bos.life)

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for bos in boss:
            if bos.state == "stop" and tmr%bos.interval == 0:
                # ボスが停止状態に入ったら，intervalに応じて羽投下
                wings.add(Wing())

        for bos in pg.sprite.groupcollide(boss, eggs, False, True).keys():
            if bos.state == "stop":
                bos.life -= 1
                if bos.life <= 0:
                    exps.add(Explosion(bos, 200))
                    bos.kill()

        for emy in pg.sprite.groupcollide(emys, eggs, False, True):
            emy.hp -= 1
            if emy.hp <= 0:
                emy.kill()
                exps.add(Explosion(emy, 100))
                print("item added")
                score.value += 10
                bird.change_img(6, screen)
                # 敵を倒した時、30%の確率でアイテムをドロップ
                if random.random() < 0.3:
                    items.add(Item(emy.rect))

            else:
                emy.damage = 5

        for bomb in pg.sprite.groupcollide(bombs, eggs, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            life.num -= 1

            if life.num <= 0:
                bird.change_img(8, screen)
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        # こうかとんとアイテムの衝突判定（拾ったときの効果）
        for item in pg.sprite.spritecollide(bird, items, True):
            if item.kind == "Score":
                score.value += 100  # スコア+100ボーナス
            elif item.kind == "Speed":
                bird.speed += 2     # こうかとんの移動速度が2アップ
            elif item.kind == "Life":
                life.num += 1       # 残機が1回復
                
        for wing in pg.sprite.spritecollide(bird, wings, True):
            life.num -= 1

            if life.num <= 0:
                bird.change_img(8, screen)
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        for emy in pg.sprite.spritecollide(bird, emys, True):
            life.num -= 1

            if life.num <= 0:
                bird.change_img(8, screen)
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        
         # こうかとんとアイテムの衝突判定（拾ったときの効果）
        for item in pg.sprite.spritecollide(bird, items, True):
            if item.kind == "Score":
                score.value += 100  # スコア+100ボーナス
            elif item.kind == "Speed":
                bird.speed += 2     # こうかとんの移動速度が2アップ
            elif item.kind == "Life":
                life.num += 1       # 残機が1回復

        bird.update(key_lst, screen)
        eggs.update()
        eggs.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        items.update()      # アイテムの移動状態更新
        items.draw(screen)   # アイテムを画面に描画
        score.update(screen)
        life.update(screen)
        boss.update()
        boss.draw(screen)
        wings.update()
        wings.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
