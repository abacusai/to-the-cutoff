while true
do
    echo "Launching"
    nohup python codeforces_scraper.py & 
    echo "Sleeping"
    AGE=0
    DURATION=0
    while [ $AGE -lt 10 ] || [ $DURATION -lt 20 ]
    do
        sleep 1
        ((DURATION=DURATION+1))
        AGE=$(perl -le '$d=shift;chomp($f=(`ls -t $d/*`)[0]);print 24*60*60*-M$f' codeforces_folder/)
        echo $AGE
    done
    echo "Killing"
    kill -9 $(ps -aux | grep codeforces_scraper.py | head -n 1 | awk '{print $2}')
done

# script used to overcome unknown crashes in scraper