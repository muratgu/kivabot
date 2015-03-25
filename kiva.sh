set PATH=/home/muratgu/local/bin:/usr/local/bin:/usr/bin:/bin
cd /home/muratgu/muratgu.com/kiva
kiva=$(< .kiva)
python ./kivabot.py $kiva 